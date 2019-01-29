#!/usr/bin/env python

# pip install pyyaml

# https://docs.python.org/3/library/functions.html#exec
# https://pyyaml.org/wiki/PyYAMLDocumentation

# run with "cloud" convention:
#   python3 ./test_sample.py convention/cloud/ex.language.test.yaml convention/cloud/cloud.py testdata/googleapis
#
# run with "manifest" convention (still need to change sample.manifest to a real manifest of the test samples; this fails at the moment because of that):
#  python3 ./test_sample.py convention/manifest/ex.language.test.yaml  convention/manifest/id_by_region.py convention/manifest/sample.manifest

import logging
import os
import string
import sys
import testcase
import yaml

import testenv

def main():
  logging.basicConfig(level=logging.INFO)
  logging.info("argv: {}".format(sys.argv))

  config_files, test_files, base_dirs = read_args(sys.argv)
  environment_registry = testenv.from_files(config_files, base_dirs)

  test_suites = gather_test_suites(test_files)

  logging.info("envs: {}".format(environment_registry.get_names()))

  run_passed = True
  for environment in environment_registry.list():
    environment.setup()

    for suite_num, suite in enumerate(test_suites):
      if not suite.get("enabled", True):
        continue
      setup = suite.get("setup", "")
      teardown = suite.get("teardown", "")
      suite_name = suite.get("name","")
      print("==== SUITE {}:{}:{} START  ==========================================".format(environment.name, suite_num, suite_name))
      print("     {}".format(suite["source"]))
      suite_passed = True
      for idx, case in enumerate(suite["cases"]):
        this_case = testcase.TestCase(environment, idx, case["id"], setup, case["spec"], teardown)
        suite_passed &=this_case.run()
      if suite_passed:
        print("==== SUITE {}:{}:{} SUCCESS ========================================".format(environment.name, suite_num, suite_name))
      else:
        print("==== SUITE {}:{}:{} FAILURE ========================================".format(environment.name, suite_num, suite_name))
      run_passed &= suite_passed

    environment.teardown()
  if not run_passed:
    exit(-1)

# TODO: need to change this to either
#   - always require manifest file
#   OR
#   - have something like test_sample testplan.yaml -e="env.py:env.py" manifest....
#    using argparse.REMAINDER for the manifests. This way the main program does not need to know about manifests. As far as it's concened, these are just args to the environments
#
# cf https://docs.python.org/3/library/argparse.html
def read_args(argv):
  config_files = []
  test_files = []
  base_dirs = []
  for filename in argv[1:]:
    filepath = os.path.abspath(filename)
    if os.path.isdir(filepath):
      base_dirs.append(filepath)
      continue

    ext = os.path.splitext(filename)[-1]
    if ext == ".py":
      config_files.append(filepath)
    elif ext == ".yaml":
      test_files.append(filepath)
    else:
      # TODO: Fix this!
      base_dirs.append(filepath)
      # msg = 'unknown file type: "{}"'.format(filename)
      # logging.critical(msg)
      # raise ValueError(msg)
  return config_files, test_files, base_dirs

def gather_test_suites(test_files):

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


#  eval(spec["test"]["case"])

if __name__== "__main__":
  main()
