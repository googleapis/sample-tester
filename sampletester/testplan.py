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

import copy
import logging
import re
import yaml


class Wrapper:

  def __init__(self):
    self.start_time = None
    self.end_time = None
    self.num_errors = 0
    self.num_failures = 0
    self.selected_to_run = True

    # whether we attempted to execute this Wrapper
    self.attempted = False

    # whether we finished executing this Wrapper (even if with errors). This is
    # important so that we don't print premature status messages as we go,
    # before the Wrapper has finished executing.
    self.completed = False

  def update_times(self, starting, ending):
    if not self.start_time or starting < self.start_time:
      self.start_time = starting
    if not self.end_time or ending > self.end_time:
      self.end_time = ending

  def duration(self):
    return self.end_time - self.start_time

  def success(self):
    return self.num_errors == 0 and self.num_failures == 0

  def selected(self):
    return self.selected_to_run


class Environment(Wrapper):

  def __init__(self, env_config, test_suites, env_filter):
    super().__init__()
    self.config = env_config
    self.suites = copy.deepcopy(test_suites)
    self.num_failing_cases = 0
    self.num_failing_suites = 0
    self.num_erroring_cases = 0
    self.num_erroring_suites = 0
    self.selected_to_run = passes_filter(env_filter, self.name())

  def name(self):
    return self.config.name()



class Suite(Wrapper):

  def __init__(self, suite_config, suite_filter, case_filter):
    super().__init__()
    self.config = copy.deepcopy(suite_config)
    self.cases = [
        TestCase(test_config, case_filter)
        for test_config in suite_config.get(SUITE_CASES, [])
    ]
    self.config[SUITE_CASES] = None
    self.num_failing_cases = 0
    self.num_erroring_cases = 0
    self.selected_to_run = passes_filter(suite_filter, self.name())

  def selected(self):
    return self.enabled and super().selected()

  def enabled(self):
    return self.config.get(SUITE_ENABLED, True)

  def setup(self):
    return self.config.get(SUITE_SETUP, "")

  def teardown(self):
    return self.config.get(SUITE_TEARDOWN, "")

  def name(self):
    return self.config.get(SUITE_NAME, "")

  def source(self):
    return self.config[SUITE_SOURCE]


class TestCase(Wrapper):

  def __init__(self, test_config, case_filter):
    super().__init__()
    self.config = copy.deepcopy(test_config)
    self.runner = None
    self.selected_to_run = passes_filter(case_filter, self.name())

  def name(self):
    return self.config.get(CASE_NAME, "(missing name)")

  def spec(self):
    return self.config.get(CASE_SPEC, "")

def passes_filter(filter: str, name: str):
  if not filter:
    return True
  found = re.search(filter, name)
  return found is not None


class Visitor:
  """Visit a `Wrapper` hierarchy.

  `Manager` uses the interface provided by this class to visit a `Wrapper`
  hierarchy.

  Each visit function returns a visitor or two to the next level of the
  hierarchy, or `None` if the next level of the hierarchy is not to be traversed
  (for example, we don't want to traverse test cases in a disabled test suite).

  The signatures in this class are what `Manager` expects to call, and what
  should be returned from the parents' visit function. However, as long as these
  return values match the signatures, the specific methods in subclasses can
  vary.
  """

  # To parallelize any of these traversals, we could modify the parent visitor
  # to return a flag determining whether parallelization is allowed. For
  # example, visit_suite can return true to signal that the loop over testcases
  # can be parallelized.

  def start_visit(self):
    return self.visit_environment, self.visit_environment_end

  def visit_environment(self, environment: Environment, doit: bool):
    return self.visit_suite, self.visit_suite_end

  def visit_suite(self, idx: int, suite: Suite, doit: bool):
    return self.visit_test_case

  def visit_testcase(self, idx: int, testcase: TestCase, doit: bool):
    pass

  def visit_suite_end(self, idx: int, suite: Suite, doit: bool):
    pass

  def visit_environment_end(self, environment: Environment, doit: bool):
    pass

  def end_visit(self):
    return True

class MultiVisitor(Visitor):
  """Applies multiple visitors in order at each level of a visit.
  """

  def __init__(self, *visitors: Visitor):
    self.visitors = visitors

  def start_visit(self):
    start_end = [visitor.start_visit() for visitor in self.visitors if visitor]
    start = [fn[0] for fn in start_end]
    end = [fn[1] for fn in start_end]
    return (lambda env, do_env: self.visit_environment(env, do_env, start),
            lambda env, do_env: self.visit_environment_end(env, do_env, end))

  def visit_environment(self, environment: Environment, doit: bool, visit_fns):
    start_end = [visit(environment, doit) for visit in visit_fns if visit]
    start = [fn[0] for fn in start_end]
    end = [fn[1] for fn in start_end]
    return (lambda idx, suite, do_suite: self.visit_suite(idx, suite,
                                                          do_suite, start),
            lambda idx, suite, do_suite: self.visit_suite_end(idx, suite,
                                                              do_suite, end))

  def visit_suite(self, idx: int, suite: Suite, doit: bool, visit_fns):
    start = [visit(idx, suite, doit) for visit in visit_fns if visit]
    return lambda idx, testcase, do_case: self.visit_testcase(idx, testcase,
                                                              do_case, start)

  def visit_testcase(self, idx: int, testcase: TestCase, doit: bool,
                     visit_fns):
    for visit in visit_fns:
      if visit:
        visit(idx, testcase, doit)

  def visit_suite_end(self, idx: int, suite: Suite, doit: bool, visit_fns):
    for visit in visit_fns:
      if visit:
        visit(idx, suite, doit)

  def visit_environment_end(self, environment: Environment, doit: bool,
                            visit_fns):
    for visit in visit_fns:
      if visit:
        visit(environment, doit)

  def end_visit(self):
    results = [visitor.end_visit() for visitor in self.visitors]
    return all(results)


SUITE_ENABLED = "enabled"
SUITE_SETUP = "setup"
SUITE_TEARDOWN = "teardown"
SUITE_NAME = "name"
SUITE_SOURCE = "source"
SUITE_CASES = "cases"
CASE_NAME = "name"
CASE_SPEC = "spec"

class Manager:

  def __init__(self, environment_registry, test_suites, env_filter:str = None):
    self.test_suites = test_suites

    logging.debug("envs: {}".format(environment_registry.get_names()))
    self.environments = [Environment(env, test_suites, env_filter)
                         for env in environment_registry.list()]

  def accept(self, visitor: Visitor):
    visit_environment, visit_environment_end = visitor.start_visit()
    if not visit_environment:
      return visitor.end_visit()

    run_passed = True
    for env in self.environments:
      do_env = env.selected()
      visit_suite, visit_suite_end = visit_environment(env, do_env)
      if not visit_suite:
        continue

      for suite_num, suite in enumerate(env.suites):
        do_suite = do_env and suite.selected()
        visit_testcase = visit_suite(suite_num, suite, do_suite)
        if not visit_testcase:
          continue

        for idx, case in enumerate(suite.cases):
          do_case = do_suite and case.selected()
          visit_testcase(idx, case, do_case)

        if visit_suite_end is not None:
          visit_suite_end(suite_num, suite, do_suite)

      if visit_environment_end:
        visit_environment_end(env, do_env)

    return visitor.end_visit()


def suite_configs_from(test_files):

  # TODO(vchudnov): Append line number info to aid in error messages
  # cf: https://stackoverflow.com/a/13319530
  all_suites = []
  for filename in test_files:
    logging.info('Reading test file "{}"'.format(filename))
    with open(filename, "r") as stream:
      spec = yaml.load(stream, Loader=yaml.SafeLoader)
      these_suites = spec["test"]["suites"]
      for suite in these_suites:
        suite["source"] = filename
      all_suites.extend(these_suites)
  return all_suites


def suite_objects_from(all_suites, suite_filter = None, case_filter = None):
  return [Suite(spec, suite_filter, case_filter) for spec in all_suites]


def suites_from(test_files, suite_filter = None, case_filter = None):
  return suite_objects_from(suite_configs_from(test_files), suite_filter, case_filter)
