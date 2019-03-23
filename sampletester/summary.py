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

from enum import Enum
import os
import sys

from sampletester import testplan

class Detail(Enum):
  NONE=1
  BRIEF=2
  FULL=3

class SummaryVisitor(testplan.Visitor):
  """Print a (running) summary of test case execution.

  The summary is printed with indentation for environments, suites, and
  test cases. By default, the summary is printed as lines are recorded, unless
  `progress_out == None` is specified in `__init__(...)`. The full output
  accumulated is available via `output()`.
  """

  def __init__(self, verbosity, show_errors,
               progress_out=sys.stderr,
               debug=False):
    self.verbosity = verbosity
    self.show_errors = show_errors
    self.lines = []
    self.indent = '  '
    self.progress_out = progress_out if progress_out else os.devnull
    self.debug = debug

  def visit_environment(self, environment: testplan.Environment, doit: bool):
    if self.verbosity == Detail.NONE and (environment.success() or not self.show_errors):
      return None, None

    name = environment.name()
    status = self.status_str(environment, doit)
    if not status:
      return None, None

    self.append_lines('{}: Test environment: "{}"'.format(status, name))
    return self.visit_suite, None

  def visit_suite(self, idx, suite: testplan.Suite, doit:bool):
    name = suite.name()
    status = self.status_str(suite, doit)
    if not status:
      return None

    self.append_lines(self.indent + '{}: Test suite: "{}"'.format(status, name))
    return self.visit_testcase

  def visit_testcase(self, idx, tcase: testplan.TestCase, doit: bool):
    name = tcase.name()
    runner = tcase.runner
    status = self.status_str(tcase, doit)
    if not status:
      return

    self.append_lines(self.indent * 2 + '{}: Test case: "{}"'
                      .format(status, name))
    if runner and (self.verbosity == Detail.FULL or (self.show_errors and not tcase.success())):
      self.append_lines(runner.get_output(6, '| '))
    if self.debug and runner:
      for error in runner.get_errors():
        self.append_lines('DEBUGGING: Error "{}":\n{}'.format(error[0],error[1]))

  def output(self):
    return '\n'.join(self.lines)

  def append_lines(self, str):
    print(str, file=self.progress_out)
    self.lines.append(str)

  def status_str(self, obj, doit):
    """Returns the status to print for a given object, or None if no status is to
    be displayed given the verbosity settings.
    """
    if not doit:
      return 'SKIPPED'
    if not obj.attempted:
      if self.verbosity == Detail.FULL:
        return 'PREEMPTED' # by an error
      return None
    if not obj.completed:
      return 'RUNNING'
    return 'PASSED' if obj.success() else 'FAILED'
