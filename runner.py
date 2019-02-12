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
import caserunner
import yaml
import testplan


class Visitor(testplan.Visitor):

  def __init__(self):
    self.run_passed = True

  def start_visit(self):
    logging.info("========== Running test!")
    return self.visit_environment, self.visit_environment_end

  def visit_environment(self, environment):
    environment.config.setup()
    return (lambda idx, suite: self.visit_suite(idx, suite, environment),
            lambda idx, suite: self.visit_suite_end(idx, suite, environment))

  def visit_suite(self, idx, suite, environment):
    if not suite.enabled():
      return None
    logging.info(
        "\n==== SUITE {}:{}:{} START  =========================================="
        .format(environment.name(), idx, suite.name()))
    logging.info("     {}".format(suite.source()))
    return lambda idx, testcase: self.visit_testcase(idx, testcase, environment.
                                                     config, suite)

  def visit_testcase(self, idx, tcase, environment, suite):
    case_runner = caserunner.TestCase(environment, idx, tcase.name(),
                                      suite.setup(), tcase.spec(),
                                      suite.teardown())
    tcase.runner = case_runner
    case_runner.run()
    tcase.num_failures += len(case_runner.failures)
    suite.num_failures += tcase.num_failures
    if tcase.num_failures > 0:
      suite.num_failing_cases += 1

    tcase.num_errors += len(case_runner.errors)
    suite.num_errors += tcase.num_errors
    if tcase.num_errors > 0:
      suite.num_erroring_cases += 1

    tcase.update_times(case_runner.start_time, case_runner.end_time)
    suite.update_times(case_runner.start_time, case_runner.end_time)

  def visit_suite_end(self, idx, suite, environment):
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

  def visit_environment_end(self, environment):
    if not environment.success():
      self.run_passed = False
    environment.config.teardown()

  def end_visit(self):
    logging.info("========== Finished running test")
    return self.success()

  def success(self):
    return self.run_passed
