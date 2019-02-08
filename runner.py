import logging
import testcase
import yaml


def run(environment_registry, test_suites):

  logging.debug("envs: {}".format(environment_registry.get_names()))

  SUITE_ENABLED="enabled"
  SUITE_SETUP="setup"
  SUITE_TEARDOWN="teardown"
  SUITE_NAME="name"
  SUITE_SOURCE="source"
  SUITE_CASES="cases"
  CASE_NAME="name"
  CASE_SPEC="spec"

  run_passed = True
  for environment in environment_registry.list():
    environment.setup()

    for suite_num, suite in enumerate(test_suites):
      if not suite.get(SUITE_ENABLED, True):
        continue
      setup = suite.get(SUITE_SETUP, "")
      teardown = suite.get(SUITE_TEARDOWN, "")
      suite_name = suite.get(SUITE_NAME,"")
      print("\n==== SUITE {}:{}:{} START  ==========================================".format(environment.name(), suite_num, suite_name))
      print("     {}".format(suite[SUITE_SOURCE]))
      suite_passed = True
      for idx, case in enumerate(suite[SUITE_CASES]):
        this_case = testcase.TestCase(environment, idx,
                                      case.get(CASE_NAME, "(missing name)"),
                                      setup,
                                      case.get(CASE_SPEC,""),
                                      teardown)
        suite_passed &= this_case.run()
      if suite_passed:
        print("==== SUITE {}:{}:{} SUCCESS ========================================".format(environment.name(), suite_num, suite_name))
      else:
        print("==== SUITE {}:{}:{} FAILURE ========================================".format(environment.name(), suite_num, suite_name))
      print()
      run_passed &= suite_passed

    environment.teardown()
    return run_passed

def suites_from(test_files):

  # TODO(vchudnov): Append line number info to aid in error messages
  # cf: https://stackoverflow.com/a/13319530
  all_suites = []
  for filename in test_files:
    logging.info('Reading test file "{}"'.format(filename))
    with open(filename, 'r') as stream:
      spec = yaml.load(stream)
      these_suites = spec["test"]["suites"]
      for suite in these_suites:
        suite["source"] = filename
      all_suites.extend(these_suites)
  return all_suites
