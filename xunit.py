import testplan

# TODO(vchudnov): Use XML library

class XUnitVisitor(testplan.Visitor):
  def __init__(self):
    self.current_environment = None

  def visit_environment(self, environment):
    self.current_environment = environment
    return self.visit_suite, self.visit_suite_end

  def visit_suite(self, idx, suite):
    print('<testsuite name="{}: {}" errors={}>'.format(suite.name(), self.current_environment.name(), suite.num_errors))
    return self.visit_testcase

  def visit_testcase(self, idx, tcase):
    print('  <testcase name="{}" errors={}>'.format(tcase.name(), tcase.num_errors))
    print('    <system-out>{}</system-out>'.format(tcase.runner.get_output(6)))
    print('  </testcase>')

  def visit_suite_end(self, idx, suite):
    print('</testsuite>')

  def visit_environment(self, environment):
    self.current_environment = environment
    return self.visit_suite, self.visit_suite_end

  def end_visit(self):
    pass
