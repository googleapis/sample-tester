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

import testplan
from enum import Enum

class Detail(Enum):
  NONE=1
  BRIEF=2
  FULL=3

class SummaryVisitor(testplan.Visitor):

  def __init__(self, verbosity, show_errors):
    self.verbosity = verbosity
    self.show_errors = show_errors
    self.lines = []
    self.indent = '  '

  def visit_environment(self, environment: testplan.Environment, doit: bool):
    if self.verbosity == Detail.NONE and (environment.success() or not self.show_errors):
      return None, None

    name = environment.name()
    status = self.status_str(environment, doit)
    if not status:
      return None, None

    self.lines.append('{}: Test environment: "{}"'.format(status, name))
    return self.visit_suite, None

  def visit_suite(self, idx, suite: testplan.Suite, doit:bool):
    name = suite.name()
    status = self.status_str(suite, doit)
    if not status:
      return None

    self.lines.append(self.indent + '{}: Test suite: "{}"'.format(status, name))
    return self.visit_testcase

  def visit_testcase(self, idx, tcase: testplan.TestCase, doit: bool):
    name = tcase.name()
    runner = tcase.runner
    status = self.status_str(tcase, doit)
    if not status:
      return

    self.lines.append(self.indent * 2 + '{}: Test case: "{}"'
                      .format(status, name))
    if runner and (self.verbosity == Detail.FULL or (self.show_errors and not tcase.success())):
      self.lines.append(runner.get_output(6, '| '))

  def end_visit(self):
    return '\n'.join(self.lines)

  # Returns the status to print for a given object, or None if no status is to
  # be displayed given the verbosity settings.
  def status_str(self, obj, doit):
    if not doit:
      return 'SKIPPED'
    if not obj.attempted:
      if self.verbosity == Detail.FULL:
        return 'PREEMPTED'
      return None
    return 'PASSED' if obj.success() else 'FAILED'
