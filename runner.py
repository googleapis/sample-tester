import logging
import testcase
import yaml
import testplan

class RunVisitor(testplan.Visitor):
  SUCCESS = '_success'

  def __init__(self):
    self.run_passed = True

  def start_visit(self):
    print("========== Running test!")
    return self.visit_environment, self.visit_environment_end

  def visit_environment(self, environment):
    environment['test_env'].setup()
    environment[self.SUCCESS] = True
    return (lambda idx, suite: self.visit_suite(idx, suite, environment),
            lambda idx, suite: self.visit_suite_end(idx, suite, environment))

  def visit_suite(self, idx, suite, environment):
    if not suite.get(testplan.SUITE_ENABLED, True):
      return None
    setup = suite.get(testplan.SUITE_SETUP, "")
    teardown = suite.get(testplan.SUITE_TEARDOWN, "")
    suite_name = suite.get(testplan.SUITE_NAME,"")
    print("\n==== SUITE {}:{}:{} START  ==========================================".format(environment['test_env'].name(), idx, suite_name))
    print("     {}".format(suite[testplan.SUITE_SOURCE]))
    suite[self.SUCCESS] = True
    return lambda idx, testcase: self.visit_testcase(idx, testcase, environment['test_env'], suite, setup, teardown)

  def visit_testcase(self, idx, tcase, environment, suite, setup, teardown):
    this_case = testcase.TestCase(environment, idx,
                                  tcase.get(testplan.CASE_NAME, "(missing name)"),
                                  setup,
                                  tcase.get(testplan.CASE_SPEC,""),
                                  teardown)
    tcase['_runner'] = this_case
    tcase[self.SUCCESS] = this_case.run()
    if not tcase[self.SUCCESS]:
      suite[self.SUCCESS] = False

  def visit_suite_end(self, idx, suite, environment):
    suite_name = suite.get(testplan.SUITE_NAME,"")
    if suite[self.SUCCESS]:
      print("==== SUITE {}:{}:{} SUCCESS ========================================".format(environment['test_env'].name(), idx, suite_name))
    else:
      environment[self.SUCCESS] = False
      print("==== SUITE {}:{}:{} FAILURE ========================================".format(environment['test_env'].name(), idx, suite_name))
    print()

  def visit_environment_end(self, environment):
    if not environment[self.SUCCESS]:
      self.run_passed = False
    environment['test_env'].teardown()

  def end_visit(self):
    print("========== Finished running test")
    return self.run_passed
