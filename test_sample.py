#!/usr/bin/env python

# pip install pyyaml

# https://docs.python.org/3/library/functions.html#exec
# https://pyyaml.org/wiki/PyYAMLDocumentation

import logging
import os.path
import string
import sys
import testcase
import yaml

def main():
  logging.basicConfig(level=logging.INFO)
  logging.info("argv: {}".format(sys.argv))

  config_files, test_files = read_args(sys.argv)
  environments = create_environments(config_files)
  test_suites = gather_test_suites(test_files)

  run_passed = True
  for suite_num, suite in enumerate(test_suites):
    if not suite.get("enabled", True):
      continue
    setup = suite.get("setup", "")
    teardown = suite.get("teardown", "")
    suite_name = suite.get("name","")
    suite_passed = True
    for idx, case in enumerate(suite["cases"]):
      this_case = testcase.TestCase(idx, case["id"], setup, case["spec"], teardown)
      suite_passed &=this_case.run()
    if suite_passed:
      print("==== SUITE {}:{} SUCCESS ========================================".format(suite_num, suite_name))
    else:
      print("==== SUITE {}:{} FAILURE ========================================".format(suite_num, suite_name))
    run_passed &= suite_passed
  if not run_passed:
    exit(-1)


def read_args(argv):
  config_files = []
  test_files = []
  for filename in argv[1:]:
    ext = os.path.splitext(filename)[-1]
    if ext == ".py":
      config_files.append(filename)
    elif ext == ".yaml":
      test_files.append(filename)
    else:
      msg = 'unknown file type: "{}"'.format(filename)
      logging.critical(msg)
      raise ValueError(msg)
  return config_files, test_files

# TODO(vchudnov): Move this to an "environment" module
def create_environments(config_files):
  environments = []
  for filename in config_files:
    logging.info('Reading config file "{}"'.format(filename))
    # TODO(vchudnov) Pass the `register_test_environment()` function as a local
    # symbol, and have that function modify `environments`
    exec(open(filename).read())
  return environments

def gather_test_suites(test_files):
  suites = []
  for filename in test_files:
    logging.info('Reading test file "{}"'.format(filename))
    with open(filename, 'r') as stream:
      spec = yaml.load(stream)
      suites.extend(spec["test"]["suites"])
  return suites


#  eval(spec["test"]["case"])

if __name__== "__main__":
  main()
