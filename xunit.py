import testplan

# TODO(vchudnov): Use XML library

class Visitor(testplan.Visitor):
  def __init__(self):
    self.environment = None

  def visit_environment(self, environment):
    self.environment = environment
    return self.visit_suite, self.visit_suite_end

  def visit_suite(self, idx, suite):
    print('<testsuite name="{}: {}" errors={}>'
          .format(self.environment.config.adjust_suite_name(suite.name()),
                  self.environment.name(), suite.num_errors))
    return self.visit_testcase

  def visit_testcase(self, idx, tcase):
    print('  <testcase name="{}" errors={}>'
          .format(self.environment.config.adjust_suite_name(tcase.name()), tcase.num_errors))
    print('    <system-out>{}</system-out>'.format(tcase.runner.get_output(6)))
    print('  </testcase>')

  def visit_suite_end(self, idx, suite):
    print('</testsuite>')

  def visit_environment(self, environment):
    self.environment = environment
    return self.visit_suite, self.visit_suite_end

  def end_visit(self):
    pass

# TODO: Add time stamp and case/suite duration, as per https://stackoverflow.com/a/9410271
