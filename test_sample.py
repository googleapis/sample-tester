#!/usr/bin/env python

# pip install pyyaml

# https://docs.python.org/3/library/functions.html#exec
# https://pyyaml.org/wiki/PyYAMLDocumentation

import yaml
import uuid
import string
import subprocess


def main():
  with open("test_spec.yaml", 'r') as stream:
    try:
        spec = yaml.load(stream)
    except yaml.YAMLError as exc:
        print(exc)

  run_passed = True
  for suite in spec["test"]["suites"]:
    setup = suite["setup"]
    teardown = suite["teardown"]
    suite_passed = True
    for idx, case in enumerate(suite["cases"]):
      suite_passed &=run_test_case(idx, case["id"], setup, case["code"], teardown)
    if suite_passed:
      print("==== SUITE SUCCESS ========================================")
    else:
      print("==== SUITE FAILURE ========================================")
    run_passed &= suite_passed
  if not run_passed:
    exit(-1)

class TestError(Exception):
  pass

def run_test_case(idx,label, setup, case, teardown):

  case_failure = []
  def record_failure(status, message):
    nonlocal case_failure
    case_failure.append((status,message))

  def expect(condition, message):
    if not condition:
      record_failure("FAILED EXPECTATION", message)

  def fail():
    expect(False, "failure")

  def require(condition, message):
    nonlocal case_failure
    if not condition:
      record_failure("FAILED REQUIREMENT", message)
      raise TestError

  def abort():
    require(False, "abort called")

  output = ""
  def print_out(msg):
    nonlocal output
    #    output += str(msg) + "\n"
    try:
      output += str(msg) + "\n"
    except Exception as e:
      raise

  def call_allow_error(cmd):
    try:
      print_out("# Calling: " + cmd)
      out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
      return_code = 0
    except subprocess.CalledProcessError as e:
      return_code = e.returncode
      out = e.output
      # return return_code, out
    except Exception as e:
      raise
    finally:
      return return_code, out.decode("utf-8")

  def call_no_error(cmd):
    return_code, out = call_allow_error(cmd)
    require(return_code == 0, "call failed: \"{0}\"".format(cmd))
    return out

  localVars={
      # Meta info  about the test case
      "testcase_num":idx,
      "testcase_id": label,

      # Functions to execute processes
      "call": call_no_error,
      "call_may_fail": call_allow_error,

      # Other functions available to the test suite
      "uuid": uuid.uuid4,
      "print":print_out,

      # Function to fail the test
      "fail": fail,
      "expect": expect,
      "abort": abort,
      "require": require,
      }

  status_message = ""
  print("==== Test case {:d}: \"{:s}\"".format(idx,label), end="")

  for stage in [("SETUP", setup), ("TEST", case), ("TEARDOWN", teardown)]:
    try:
      print_out("### Test case {0}\n".format(stage[0]))
      exec(stage[1],localVars)
    except TestError:
      pass
    except Exception as e:
      record_failure("UNHANDLED EXCEPTION (check state: clean-up did not finish)", stage[0])
      break

  if len(case_failure) > 0:
    print(" FAILED ====================")
    for failure in case_failure:
      print("    {0} \"{1}\"".format(failure[0], failure[1]))
    print("    Output:")
    print(reindent(output, 4, "| ")+"\n")
  else:
    print(" PASSED ==============================")

  return len(case_failure) == 0

# heavily adapted from from https://www.oreilly.com/library/view/python-cookbook/0596001673/ch03s12.html
def reindent(s, numSpaces, prompt):
    s = s.split('\n')
    s = [(numSpaces * ' ') + prompt + line for line in s]
    s = "\n".join(s)
    return s

#  eval(spec["test"]["case"])

if __name__== "__main__":
  main()
