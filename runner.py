import logging
import testcase
import yaml
import testplan

class RunVisitor(testplan.Visitor):

  def __init__(self):
    self.run_passed = True

  def start_visit(self):
    logging.info("========== Running test!")
    return self.visit_environment, self.visit_environment_end

  def visit_environment(self, environment):
    environment['test_env'].setup()
    environment[testplan.SUCCESS] = True
    return (lambda idx, suite: self.visit_suite(idx, suite, environment),
            lambda idx, suite: self.visit_suite_end(idx, suite, environment))

  def visit_suite(self, idx, suite, environment):
    if not suite.get(testplan.SUITE_ENABLED, True):
      return None
    setup = suite.get(testplan.SUITE_SETUP, "")
    teardown = suite.get(testplan.SUITE_TEARDOWN, "")
    suite_name = suite.get(testplan.SUITE_NAME,"")
    logging.info("\n==== SUITE {}:{}:{} START  ==========================================".format(environment['test_env'].name(), idx, suite_name))
    logging.info("     {}".format(suite[testplan.SUITE_SOURCE]))
    suite[testplan.SUCCESS] = True
    return lambda idx, testcase: self.visit_testcase(idx, testcase, environment['test_env'], suite, setup, teardown)

  def visit_testcase(self, idx, tcase, environment, suite, setup, teardown):
    this_case = testcase.TestCase(environment, idx,
                                  tcase.get(testplan.CASE_NAME, "(missing name)"),
                                  setup,
                                  tcase.get(testplan.CASE_SPEC,""),
                                  teardown)
    tcase['_runner'] = this_case
    tcase[testplan.SUCCESS] = this_case.run()
    if not tcase[testplan.SUCCESS]:
      suite[testplan.SUCCESS] = False

  def visit_suite_end(self, idx, suite, environment):
    suite_name = suite.get(testplan.SUITE_NAME,"")
    if suite[testplan.SUCCESS]:
      logging.info("==== SUITE {}:{}:{} SUCCESS ========================================".format(environment['test_env'].name(), idx, suite_name))
    else:
      environment[testplan.SUCCESS] = False
      logging.info("==== SUITE {}:{}:{} FAILURE ========================================".format(environment['test_env'].name(), idx, suite_name))

  def visit_environment_end(self, environment):
    if not environment[testplan.SUCCESS]:
      self.run_passed = False
    environment['test_env'].teardown()

  def end_visit(self):
    logging.info("========== Finished running test")
    return self.run_passed
