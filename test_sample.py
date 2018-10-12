#!/usr/bin/env python

# pip install pyyaml

# https://docs.python.org/3/library/functions.html#exec
# https://pyyaml.org/wiki/PyYAMLDocumentation

import yaml
import uuid
import string


def main():
  print("Hello world!")
  with open("test_spec.yaml", 'r') as stream:
    try:
        spec = yaml.load(stream)
    except yaml.YAMLError as exc:
        print(exc)
  print(spec)
  print("Evaluating:")
  run_passed = True
  for suite in spec["test"]["suites"]:
    setup = suite["setup"]
    teardown = suite["teardown"]
    suite_passed = True
    for idx, case in enumerate(suite["cases"]):
      suite_passed &=run_test_case(idx, setup, case, teardown)
    if suite_passed:
      print("==== SUITE SUCCESS ========================================")
    else:
      print("==== SUITE FAILURE ========================================")
    run_passed &= suite_passed
  if not run_passed:
    exit(-1)

def run_test_case(idx,setup, case, teardown):

  case_failure = ""
  def expect(condition, message):
    nonlocal case_failure
    if not condition:
      case_failure = message

  def fail():
    expect(False, "failure")

  def require(condition, message):
    nonlocal case_failure
    if not condition:
      case_failure = message
      raise Exception(message)

  def abort():
    require(False, "abort called")

  output = ""
  def print_out(msg):
    nonlocal output
    output += str(msg) + "\n"

  def call_allow_error(cmd):
    print(".......", cmd)
    try:
      out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
      print("......... {0}".out)
      return_code = 0
    except CalledProcessError as e:
      return_code = e.returncode
      out = e.output
      print("......... {0}".out)
      return return_code, out
    return return_code, out

  def call_no_error(cmd):
    print("........", cmd)
    return_code, out = call_allow_error(cmd)
    require(return_code == 0, "call failed: \"{0}\"".format(cmd))
    return out

  localVars={
      "testcase_num":idx,
      "fail": fail,
      "expect": expect,
      "abort": abort,
      "require": require,
      "uuid": uuid.uuid4,
      "printit":print_out,
      "print":print,  # just for debugging
      "callit": call_no_error,
      "call_may_fail": call_allow_error}

  status_message = ""
  print("\n==== Test case {:d}: ".format(idx), end="")
  #  print("-------- setup -----------------------------------")
  exec(setup,{},localVars)

  #  print("-------- test ------------------------------------")
  try:
    exec(case, {}, localVars)
  except Exception as e:
    status_message = "TERMINAL FAILURE"
  if len(case_failure) > 0:
    status_message = " FAILED"
    print(" FAILURE ====================")
    print("*** {0} \"{1}\"".format(status_message, case_failure))
    print("*** Output:")
    print(reindent(output, 4))
  else:
    print(" PASSED ==============================")

  #  print("-------- teardown --------------------------------")
  exec(teardown, {}, localVars)
  #  print("--------------------------------------------------")


  return len(case_failure) == 0  # should also catch issues in abort and clean up

  # from https://www.oreilly.com/library/view/python-cookbook/0596001673/ch03s12.html
def reindent(s, numSpaces):
    s = s.split('\n')
    s = [(numSpaces * ' ') + line for line in s]
    s = "\n".join(s)
    return s

#  eval(spec["test"]["case"])

if __name__== "__main__":
  main()
