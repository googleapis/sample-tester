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

import logging
import yaml

from sampletester import caserunner
from sampletester import testplan


class Visitor(testplan.Visitor):

  def __init__(self, fail_fast=False):
    self.run_passed = True
    self.fail_fast = fail_fast
    self.encountered_failure = False

  def start_visit(self):
    logging.info("========== Running test!")
    return self.visit_environment, self.visit_environment_end

  def visit_environment(self, environment: testplan.Environment, do_environment: bool):
    if not do_environment:
      logging.info('skipping environment "{}"'.format(environment.name()))
      return None, None

    if self.fail_fast and self.encountered_failure:
      logging.info('fail fast: not running environment "{}"'.format(environment.name))
      return None, None

    environment.attempted = True
    environment.config.setup()
    return (lambda idx, suite, do_suite: self.visit_suite(idx, suite, do_suite, environment),
            lambda idx, suite, do_suite: self.visit_suite_end(idx, suite, do_suite, environment))

  def visit_suite(self, idx: int, suite: testplan.Suite, do_suite: bool,
                  environment: testplan.Environment):
    if not do_suite:
      logging.info('skipping suite "{}"'.format(suite.name()))
      return None

    if self.fail_fast and self.encountered_failure:
      logging.info('fail fast: not running suite "{}"'.format(suite.name))
      return None

    suite.attempted = True
    logging.info(
        "\n==== SUITE {}:{}:{} START  =========================================="
        .format(environment.name(), idx, suite.name()))
    logging.info("     {}".format(suite.source()))
    return lambda idx, testcase, do_case: self.visit_testcase(idx, testcase,
                                                              do_case, environment, suite)

  def visit_testcase(self, idx: int, tcase: testplan.TestCase, do_case: bool,
                     environment: testplan.Environment, suite: testplan.Suite):
    if not do_case:
      logging.info('skipping case "{}"'.format(tcase.name()))
      return

    if self.fail_fast and self.encountered_failure:
      logging.info('fail fast: not running case "{}"'.format(tcase.name))
      return

    tcase.attempted = True
    case_runner = caserunner.TestCase(environment.config, idx, tcase.name(),
                                      suite.setup(), tcase.spec(),
                                      suite.teardown())
    tcase.runner = case_runner
    case_runner.run()
    num_failures = len(case_runner.failures)
    tcase.num_failures += num_failures
    suite.num_failures += tcase.num_failures
    if tcase.num_failures > 0:
      suite.num_failing_cases += 1

    num_errors = len(case_runner.errors)
    tcase.num_errors += num_errors
    suite.num_errors += tcase.num_errors
    if tcase.num_errors > 0:
      suite.num_erroring_cases += 1

    tcase.update_times(case_runner.start_time, case_runner.end_time)
    suite.update_times(case_runner.start_time, case_runner.end_time)
    self.encountered_failure = self.encountered_failure or num_errors > 0 or num_failures > 0
    tcase.completed = True

  def visit_suite_end(self, idx, suite: testplan.Suite,
                      do_suite: bool, environment: testplan.Environment):
    if suite.success():
      logging.info(
          "==== SUITE {}:{}:{} SUCCESS ========================================"
          .format(environment.name(), idx, suite.name()))
    else:
      environment.num_failures += suite.num_failures
      environment.num_failing_cases += suite.num_failing_cases
      if suite.num_failures > 0:
        environment.num_failing_suites += 1

      environment.num_errors += suite.num_errors
      environment.num_erroring_cases += suite.num_erroring_cases
      if suite.num_errors > 0:
        environment.num_erroring_suites += 1

      environment.update_times(suite.start_time, suite.end_time)
      logging.info(
          "==== SUITE {}:{}:{} FAILURE ========================================"
          .format(environment.name(), idx, suite.name()))
      suite.completed = True

  def visit_environment_end(self, environment: testplan.Environment, do_environment: bool):
    if not environment.success():
      self.run_passed = False
    environment.completed = True
    environment.config.teardown()

  def end_visit(self):
    logging.info("========== Finished running test")
    return self.success()

  def success(self):
    return self.run_passed
