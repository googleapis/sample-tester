#!/usr/bin/env python3
# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re
import unittest
import yaml

from sampletester import caserunner
from sampletester import convention
from sampletester import environment_registry
from sampletester import inputs
from sampletester import parser
from sampletester import runner
from sampletester import summary
from sampletester import testplan

_ABS_FILE = os.path.abspath(__file__)
_ABS_DIR = os.path.split(_ABS_FILE)[0]


class Visitor(testplan.Visitor):

  def __init__(self):
    self.environments = {}
    self.suites = {}
    self.cases = {}
    self.current_env = ''
    self.current_suite = ''
    self.error = None

  def visit_environment(self, env, doit=True):
    self.current_env = env.config.name()
    self.environments[self.current_env] = env
    return self.visit_suite, None

  def visit_suite(self, idx, suite, doit=True):
    self.current_suite = '{}:{}'.format(self.current_env, suite.name())
    self.suites[self.current_suite] = suite
    return self.visit_testcase

  def visit_testcase(self, idx, tcase, doit=True):
    if tcase.name() not in ['code', 'yaml']:
      self.error = 'found neither "code" nor "yaml" in case name "{}"'.format(
          tcase.name())
      return
    name = '{}:{}'.format(self.current_suite, tcase.name())
    self.cases[name] = tcase

  def end_visit(self):
    return self.error


class TestCaseRunner(unittest.TestCase):

  def setUp(self):
    self.environment_registry = environment_registry.new(
        convention.DEFAULT,
        inputs.create_indexed_docs(
            *full_paths('testdata/caserunner_test.manifest.yaml')))
    self.manager = testplan.Manager(
        self.environment_registry,
        testplan.suites_from(
            inputs.create_indexed_docs(
                *full_paths('testdata/caserunner_test.yaml'))))
    self.results = Visitor()
    self.manager.accept(testplan.MultiVisitor(runner.Visitor(),
                                              summary.SummaryVisitor(verbosity=summary.Detail.FULL,
                                                                     show_errors=True)))
    if self.manager.accept(self.results) is not None:
      self.fail('error running test plan: {}'.format(self.results.error))

  def test_all(self):
    for suite_name in list(self.results.suites.keys()):
      if 'passing' in suite_name.lower():
        self.check_success(suite_name, self.assertTrue,
                   'expected valid test suite to pass: {}'.format(suite_name))
      elif 'failing' in suite_name.lower():
        self.check_success(suite_name, self.assertFalse,
                   'expected failing test suite to fail: {}'.format(suite_name))
      else:
        self.fail(
            'found neither "passing" nor "failing" in suite name "{}"'
            .format(suite_name))

      if 'erroring' in suite_name.lower():
        self.check_error(suite_name, self.assertFalse,
                         'expected test suite to error: {}'.format(suite_name))
      else:
        self.check_error(suite_name, self.assertTrue,
                         'expected test suite to not error: {}'.format(suite_name))

  def check_success(self, suite_name, assertion, message):
    assertion(self.results.cases[suite_name + ':code'].success(),
              '{}: {}:code'.format(message, suite_name))
    assertion(self.results.cases[suite_name + ':yaml'].success(),
              '{}: {}:yaml'.format(message, suite_name))
    assertion(self.results.suites[suite_name].success(),
              '{}: {}'.format(message, suite_name))

  def check_error(self, suite_name, assertion, message):
    assertion(self.results.cases[suite_name + ':code'].num_errors == 0,
                     '{}: {}:code'.format(message, suite_name))
    assertion(self.results.cases[suite_name + ':yaml'].num_errors == 0,
                     '{}: {}:yaml'.format(message, suite_name))
    assertion(self.results.suites[suite_name].num_errors == 0,
                    '{}: {}'.format(message, suite_name))


class TestCaseRunnerSkipsCasesWhenSetupFails(unittest.TestCase):
  def setUp(self):
    self.environment_registry = environment_registry.new(
        convention.DEFAULT, inputs.create_indexed_docs())
    self.manager = testplan.Manager(
        self.environment_registry,
        testplan.suites_from(
            inputs.create_indexed_docs(
                *full_paths('testdata/caserunner_test_setup_failures.yaml'))))
    self.results = Visitor()
    self.manager.accept(testplan.MultiVisitor(runner.Visitor(fail_fast=False),
                                              summary.SummaryVisitor(verbosity=summary.Detail.FULL,
                                                                     show_errors=True)))
    if self.manager.accept(self.results) is not None:
      self.fail('error running test plan: {}'.format(self.results.error))

    self.fname_re = re.compile('^filename: (.+)$', re.MULTILINE)

  def do_test_case(self, suite_name, case_variant):
      case_name = suite_name + case_variant
      self.assertFalse(self.results.suites[suite_name].success(),
                       'expected test suite to fail: {}'.format(suite_name))
      self.assertFalse(self.results.cases[case_name].success(),
                       'expected test case to fail: {}'.format(case_name))
      case_output = self.results.cases[case_name].runner.output
      fname_match = self.fname_re.search(case_output)
      self.assertFalse(fname_match is None, 'could not extract filename in output:>>>\n{}\n<<<'.format(case_output))
      fname = fname_match.group(1)
      with open(fname) as f:
        processed = f.read()
      context = 'processed("{}", case {}):>>>\n{}\n<<<'.format(fname, case_name, processed)
      self.assertTrue('setup-before' in processed, 'expected "setup-before" in {}'.format(context))
      self.assertFalse('setup-after' in processed, 'expected "setup-after" to not be in {}'.format(context))
      self.assertFalse(case_variant in processed, 'expected "{}" to not be in {}'.format(case_variant, context))
      self.assertTrue('teardown' in processed, 'expected "teardown" in {}'.format(context))

  def test_setup_assertion_fails_suite(self):
    for suite_name in list(self.results.suites.keys()):
      self.do_test_case(suite_name, ':code')
      self.do_test_case(suite_name, ':yaml')


class TestCaseRunnerCatchExceptions(unittest.TestCase):
  def setUp(self):
    self.environment_registry = environment_registry.new(convention.DEFAULT,
                                                         inputs.create_indexed_docs())
    self.manager = testplan.Manager(
        self.environment_registry,
        testplan.suites_from(
            inputs.create_indexed_docs(
                *full_paths('testdata/caserunner_test_exception.yaml'))))
    self.results = Visitor()

  def test_keyboard_interrupt(self):
    with self.assertRaises(KeyboardInterrupt):
      self.manager.accept(runner.Visitor())

    if self.manager.accept(self.results) is not None:
      self.fail('unexpected error running test plan: {}'.format(self.results.error))
    for _, suite in self.results.suites.items():
      self.assertFalse(suite.completed, 'keyboard interrupt should cause incomplete test suite')
    for _, tcase in self.results.cases.items():
      self.assertFalse(tcase.completed, 'keyboard interrupt should cause incomplete test case')

class TestCaseRunnerNoMatchForCallTarget(unittest.TestCase):
  def setUp(self):
    self.environment_registry = environment_registry.new(
        convention.DEFAULT,
        inputs.create_indexed_docs(
            *full_paths('testdata/caserunner_test_target.manifest.yaml')))
    self.manager = testplan.Manager(
        self.environment_registry,
        testplan.suites_from(
            inputs.create_indexed_docs(
                *full_paths('testdata/caserunner_test_target.yaml'))))
    self.results = Visitor()

  def test_did_not_call(self):
    self.manager.accept(testplan.MultiVisitor(runner.Visitor(),
                                              summary.SummaryVisitor(verbosity=summary.Detail.FULL,
                                                                     show_errors=True)))
    if self.manager.accept(self.results) is not None:
      self.fail('error running test plan: {}'.format(self.results.error))
    self.assertEqual(1, self.results.environments['alps'].num_erroring_cases,
                     "expected error when they key name in 'call.target' is not present in manifest")

class TestCaseRunnerMatchesForCallTarget(unittest.TestCase):
  def setUp(self):
    self.environment_registry = environment_registry.new(
        'tag:alpine',
        inputs.create_indexed_docs(
            *full_paths('testdata/caserunner_test_target.manifest.yaml')))
    self.manager = testplan.Manager(
        self.environment_registry,
        testplan.suites_from(
            inputs.create_indexed_docs(
                *full_paths('testdata/caserunner_test_target.yaml'))))
    self.results = Visitor()

  def test_did_call(self):
    self.manager.accept(testplan.MultiVisitor(runner.Visitor(),
                                              summary.SummaryVisitor(verbosity=summary.Detail.FULL,
                                                                     show_errors=True)))
    if self.manager.accept(self.results) is not None:
      self.fail('error running test plan: {}'.format(self.results.error))
    self.assertEqual(0, self.results.environments['alps'].num_erroring_cases,
                     "expected no error when the key name in 'call.target' is present in manifest")

class TestChdir(unittest.TestCase):

  def setUp(self):
    self.environment_registry = environment_registry.new(
        convention.DEFAULT,
        inputs.create_indexed_docs(
            *full_paths('testdata/caserunner_test.chdir.manifest.yaml')))
    self.manager = testplan.Manager(
        self.environment_registry,
        testplan.suites_from(
            inputs.create_indexed_docs(
                *full_paths('testdata/caserunner_chdir_test.yaml'))))
    self.results = Visitor()
    self.manager.accept(testplan.MultiVisitor(runner.Visitor(),
                                              summary.SummaryVisitor(verbosity=summary.Detail.FULL,
                                                                     show_errors=True)))
    if self.manager.accept(self.results) is not None:
      self.fail('error running test plan: {}'.format(self.results.error))

  def test_chdir(self):
    for suite_name in list(self.results.suites.keys()):
      self.assertTrue(self.results.cases[suite_name + ':code'].success(),
                      'expected suite to pass: {}'.format(suite_name))

class TestSymbolInterpolation(unittest.TestCase):
  def test_symbol_interpolation(self):
    resolver_dict = {
        "H": "hydrogen",
        "He": "helium",
        "Li": "lithium"
    }
    resolver = lambda name: resolver_dict.get(name, '')
    self.assertEqual('Start with hydrogen, helium, and lithium',
                     caserunner.interpolate_symbols(
                         'Start with {H}, {He}, and {Li}',
                         resolver))
    self.assertEqual('Want hydrogen or ?',
                     caserunner.interpolate_symbols('Want {H} or {Ur}?',
                                                    resolver))


def full_paths(*leaf_path):
  return [os.path.join(_ABS_DIR, path) for path in leaf_path]


if __name__ == '__main__':
  unittest.main()
