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

import unittest
import runner
import os
import convention
import environment_registry
import testplan


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
    __abs_file__ = os.path.abspath(__file__)
    self.__abs_file_path__ = os.path.split(__abs_file__)[0]
    self.environment_registry = environment_registry.new(convention.DEFAULT, [])
    self.manager = testplan.Manager(
        self.environment_registry,
        self.suites_from(['testdata/caserunner_test.yaml']))
    self.results = Visitor()
    self.manager.accept(runner.Visitor())
    if self.manager.accept(self.results) is not None:
      self.fail('error running test plan: {}'.format(self.results.error))

  def path_to(self, dir):
    return os.path.join(self.__abs_file_path__, dir)

  def suites_from(self, directories):
    return testplan.suites_from([self.path_to(dir) for dir in directories])

  def test_all(self):
    for suite_name in list(self.results.suites.keys()):
      if 'Passing' in suite_name:
        self.check(suite_name, self.assertTrue,
                   'expected valid test suite to pass')
      elif 'Failing' in suite_name:
        self.check(suite_name, self.assertFalse,
                   'expected failing test suite to fail')
      else:
        self.fail(
            'found neither  "Passing" or "Failing" in suite name "{}"'.format(
                suite_name))

  def check(self, suite_name, assertion, message):
    assertion(self.results.suites[suite_name].success(), '{}: {}'.format(
        message, suite_name))
    assertion(self.results.cases[suite_name + ':code'].success(),
              '{}: {}:code'.format(message, suite_name))
    assertion(self.results.cases[suite_name + ':yaml'].success(),
              '{}: {}:yaml'.format(message, suite_name))


if __name__ == '__main__':
  unittest.main()
