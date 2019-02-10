import logging
import testcase
import yaml
import testplan

class Visitor(testplan.Visitor):

  def __init__(self):
    self.run_passed = True

  def start_visit(self):
    logging.info("========== Running test!")
    return self.visit_environment, self.visit_environment_end

  def visit_environment(self, environment):
    environment.config.setup()
    return (lambda idx, suite: self.visit_suite(idx, suite, environment),
            lambda idx, suite: self.visit_suite_end(idx, suite, environment))

  def visit_suite(self, idx, suite, environment):
    if not suite.enabled():
      return None
    logging.info("\n==== SUITE {}:{}:{} START  ==========================================".format(environment.name(), idx, suite.name()))
    logging.info("     {}".format(suite.source()))
    return lambda idx, testcase: self.visit_testcase(idx, testcase, environment.config, suite)

  def visit_testcase(self, idx, tcase, environment, suite):
    case_runner = testcase.TestCase(environment, idx,
                                    tcase.name(),
                                    suite.setup(),
                                    tcase.spec(),
                                    suite.teardown())
    tcase.runner = case_runner
    tcase.num_errors += case_runner.run()
    suite.num_errors += tcase.num_errors
    if tcase.num_errors > 0:
      suite.num_failing_cases += 1

  def visit_suite_end(self, idx, suite, environment):
    if suite.success():
      logging.info("==== SUITE {}:{}:{} SUCCESS ========================================".format(environment.name(), idx, suite.name()))
    else:
      environment.num_errors += suite.num_errors
      environment.num_failing_cases += suite.num_failing_cases
      environment.num_failing_suites += 1
      logging.info("==== SUITE {}:{}:{} FAILURE ========================================".format(environment.name(), idx, suite.name()))

  def visit_environment_end(self, environment):
    if not environment.success():
      self.run_passed = False
    environment.config.teardown()

  def end_visit(self):
    logging.info("========== Finished running test")
    return self.success()

  def success(self):
    return self.run_passed
