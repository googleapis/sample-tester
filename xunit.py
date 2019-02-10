import testplan
import html

# TODO(vchudnov): Use XML library

class Visitor(testplan.Visitor):
  def __init__(self):
    self.environment = None
    self.lines = []
    self.indent ='  '
    self.num_failures = 0
    self.num_errors = 0

  def visit_environment(self, environment):
    self.environment = environment
    return self.visit_suite, self.visit_suite_end

  def visit_suite(self, idx, suite):
    self.lines.append(self.indent + '<testsuite name="{}: {}" failures="{}" errors="{}" timestamp="{}" time="{}">'
          .format(self.environment.config.adjust_suite_name(suite.name()), self.environment.name(),
                  suite.num_failures,
                  suite.num_errors,
                  suite.start_time.isoformat(),
                  suite.duration().total_seconds()))
    return self.visit_testcase

  def visit_testcase(self, idx, tcase):
    self.lines.append(self.indent*2 + '<testcase name="{}" failures="{}" errors="{}" timestamp="{}" time="{}">'
          .format(self.environment.config.adjust_suite_name(tcase.name()),
                  tcase.num_failures,
                  tcase.num_errors,
                  tcase.start_time.isoformat(),
                  tcase.duration().total_seconds()) )
    self.lines.append('{}<system-out>{}\n{}</system-out>'
                      .format(self.indent*3,
                              html.escape(tcase.runner.get_output(8)),
                              self.indent*3))
    self.lines.append(self.indent*2 + '</testcase>')

  def visit_suite_end(self, idx, suite):
    self.lines.append(self.indent +'</testsuite>')

  def visit_environment_end(self, environment):
    self.num_failures += environment.num_failures
    self.num_errors += environment.num_errors

  def end_visit(self):
    lines = self.lines
    self.lines=['<testsuites failures="{}" errors="{}">'.format(self.num_failures, self.num_errors)]
    self.lines.extend(lines)
    self.lines.append('</testsuites>')
    return '\n'.join(self.lines)

# TODO: write <failure> elements. Do we need <error> elements?
