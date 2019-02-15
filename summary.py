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


class SummaryVisitor(testplan.Visitor):

  def __init__(self, verbose):
    self.verbose = verbose
    self.lines = []
    self.indent = '  '

  def visit_environment(self, environment):
    name = environment.name()
    self.lines.append('{}: Test environment: "{}"'.format(
        status_str(environment), name))
    return self.visit_suite, None

  def visit_suite(self, idx, suite):
    name = suite.name()
    self.lines.append(self.indent +
                      '{}: Test suite: "{}"'.format(status_str(suite), name))
    return self.visit_testcase

  def visit_testcase(self, idx, tcase):
    name = tcase.name()
    runner = tcase.runner
    self.lines.append(self.indent * 2 +
                      '{}: Test case: "{}"'.format(status_str(tcase), name))
    if self.verbose and runner:
      self.lines.append(runner.get_output(6, '| '))

  def end_visit(self):
    return '\n'.join(self.lines)


def status_str(obj):
  return 'PASSED' if obj.success() else 'FAILED'
