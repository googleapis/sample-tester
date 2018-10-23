#!/usr/bin/env python

# pip install pyyaml

# https://docs.python.org/3/library/functions.html#exec
# https://pyyaml.org/wiki/PyYAMLDocumentation

import yaml
import string
import testcase



def main():
  with open("test_spec.yaml", 'r') as stream:
    try:
        spec = yaml.load(stream)
    except yaml.YAMLError as exc:
        print(exc)

  run_passed = True
  for suite_num, suite in enumerate(spec["test"]["suites"]):
    if not suite.get("enabled", True):
      continue
    setup = suite.get("setup", "")
    teardown = suite.get("teardown", "")
    suite_name = suite.get("name","")
    suite_passed = True
    for idx, case in enumerate(suite["cases"]):
      this_case = testcase.TestCase(idx, case["id"], setup, case["code"], teardown)
      suite_passed &=this_case.run()
    if suite_passed:
      print("==== SUITE {}:{} SUCCESS ========================================".format(suite_num, suite_name))
    else:
      print("==== SUITE {}:{} FAILURE ========================================".format(suite_num, suite_name))
    run_passed &= suite_passed
  if not run_passed:
    exit(-1)




#  eval(spec["test"]["case"])

if __name__== "__main__":
  main()
