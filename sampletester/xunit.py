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

import html

from sampletester import testplan

class Visitor(testplan.Visitor):

  def __init__(self):
    self.environment = None
    self.lines = []
    self.indent = '  '
    self.num_failures = 0
    self.num_errors = 0

  def visit_environment(self, environment: testplan.Environment, doit: bool):
    if not doit or not environment.attempted:
      return None, None
    self.environment = environment
    return self.visit_suite, self.visit_suite_end

  def visit_suite(self, idx, suite: testplan.Suite, doit: bool):
    if not doit or not suite.attempted:
      return None
    self.lines.append(
        '{}<testsuite name="{}" failures="{}" errors="{}" timestamp="{}" time="{}">'
        .format(
            self.indent,
            html.escape(
                self.environment.config.adjust_suite_name(suite.name())),
            suite.num_failures, suite.num_errors, suite.start_time.isoformat(),
            suite.duration().total_seconds()))
    return self.visit_testcase

  def visit_testcase(self, idx, tcase: testplan.TestCase, doit: bool):
    if not doit or not tcase.attempted:
      return
    self.lines.append(
        '{}<testcase name="{}" failures="{}" errors="{}" timestamp="{}" time="{}">'
        .format(
            self.indent * 2,
            html.escape(
                self.environment.config.adjust_suite_name(tcase.name())),
            tcase.num_failures, tcase.num_errors, tcase.start_time.isoformat(),
            tcase.duration().total_seconds()))

    for failure in tcase.runner.get_failures():
      self.lines.append('{}<failure type="{}">'.format(
          self.indent * 3, html.escape(failure[0].lower())))
      self.lines.append('{}{}'.format(self.indent * 4, html.escape(failure[1])))
      self.lines.append('{}</failure>'.format(self.indent * 3))

    for error in tcase.runner.get_errors():
      self.lines.append('{}<error type="{}">'.format(
          self.indent * 3, html.escape(error[0].lower())))
      self.lines.append('{}{}'.format(self.indent * 4, html.escape(error[1])))
      self.lines.append('{}</error>'.format(self.indent * 3))

    self.lines.append('{}<system-out>{}\n{}</system-out>'.format(
        self.indent * 3, html.escape(tcase.runner.get_output(8)),
        self.indent * 3))

    self.lines.append(self.indent * 2 + '</testcase>')

  def visit_suite_end(self, idx, suite: testplan.Suite, doit: bool):
    if not doit or not suite.attempted:
      return
    self.lines.append('{}</testsuite>'.format(self.indent))

  def visit_environment_end(self, environment: testplan.Environment, doit: bool):
    if not doit or not environment.attempted:
      return
    self.num_failures += environment.num_failures
    self.num_errors += environment.num_errors

  def end_visit(self):
    lines = self.lines
    self.lines = [
        '<testsuites failures="{}" errors="{}">'.format(self.num_failures,
                                                        self.num_errors)
    ]
    self.lines.extend(lines)
    self.lines.append('</testsuites>\n')
    return '\n'.join(self.lines)
