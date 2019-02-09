import testplan

class SummaryVisitor(testplan.Visitor):
  def __init__(self, verbose):
    self.verbose = verbose
    self.lines = []
    self.indent = '  '

  def visit_environment(self, environment):
    name = environment.name()
    self.lines.append('{}: Environment: "{}"'.format(status_str(environment), name))
    return self.visit_suite, None

  def visit_suite(self, idx, suite):
    name = suite.name()
    self.lines.append(self.indent + '{}: Suite: "{}"'.format(status_str(suite), name))
    return self.visit_testcase

  def visit_testcase(self, idx, tcase):
    name = tcase.name()
    runner = tcase.runner
    self.lines.append(self.indent*2 + '{}: Case: "{}"'.format(status_str(tcase), name))
    if self.verbose and runner:
      self.lines.append(runner.get_output(6, '| '))

  def end_visit(self):
    return '\n'.join(self.lines)

def status_str(obj):
  return 'SUCCESS' if obj.success() else 'FAILURE'
