#!/usr/bin/env python3
import unittest
import runner
import os
import convention
import testenv
import testplan

class TestVisitor(testplan.Visitor):
  def __init__(self):
    self.environments = {}
    self.suites = {}
    self.cases = {}
    self.current_env =''
    self.current_suite=''
    self.error = None


  def visit_environment(self, env):
    self.current_env = env.config.name()
    self.environments[self.current_env] = env
    return self.visit_suite, None

  def visit_suite(self, idx, suite):
    self.current_suite = '{}:{}'.format(self.current_env,suite.name())
    self.suites[self.current_suite] = suite
    return self.visit_testcase

  def visit_testcase(self, idx, tcase):
    if tcase.name() not in ['code', 'yaml']:
      self.error = 'found neither "code" nor "yaml" in case name "{}"'.format(tcase.name())
      return
    name = '{}:{}'.format(self.current_suite,tcase.name())
    self.cases[name] = tcase

  def end_visit(self):
    return self.error


class TestTestCase(unittest.TestCase):
  def setUp(self):
    __abs_file__ = os.path.abspath(__file__)
    self.__abs_file_path__ = os.path.split(__abs_file__)[0]
    self.environment_registry = testenv.from_files([convention.default], [])
    self.manager = testplan.Manager(self.environment_registry, self.suites_from(['testdata/testcase_passing.yaml']))
    self.manager.accept(runner.RunVisitor())
    self.results = TestVisitor()
    self.manager.accept(runner.RunVisitor())
    if self.manager.accept(self.results) is not None:
      self.fail('error running test plan: {}'.format(self.results.error))

  def path_to(self, dir):
    return os.path.join(self.__abs_file_path__, dir)

  def suites_from(self, directories):
    return testplan.suites_from([self.path_to(dir) for dir in directories])

  def test_all(self):
    for suite_name in list(self.results.suites.keys()):
      if "Passing" in suite_name:
        self.check(suite_name, self.assertTrue, "expected valid test suite to pass")
      elif "Failing" in suite_name:
        self.check(suite_name, self.assertFalse, "expected failing test suite to fail")
      else:
        self.fail('found neither  "Passing" or "Failing" in suite name "{}"'.format(suite_name))



  def check(self, suite_name, assertion, message):
    assertion(self.results.suites[suite_name].success(), '{}: {}'.format(message, suite_name))
    assertion(self.results.cases[suite_name+':code'].success(), '{}: {}:code'.format(message, suite_name))
    assertion(self.results.cases[suite_name+':yaml'].success(), '{}: {}:yaml'.format(message, suite_name))

if __name__ == '__main__':
  unittest.main()
