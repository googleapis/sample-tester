import uuid
import subprocess

class TestCase:

  def __init__(self, idx, label, setup, case, teardown):
    self.case_failure = []
    self.output = ""

    self.idx = idx
    self.label = label
    self.setup = setup
    self.case = case
    self.teardown = teardown

  def get_uuid(self):
    return str(uuid.uuid4())

  def record_failure(self, status, message):
    self.case_failure.append((status,message))

  def expect(self, condition, message):
    if not condition:
      self.record_failure("FAILED EXPECTATION", message)

  def fail(self):
    self.expect(False, "failure")

  def require(self, condition, message):
    if not condition:
      self.record_failure("FAILED REQUIREMENT", message)
      raise TestError

  def abort(self):
    self.require(False, "abort called")

  def print_out(self, msg):
    #    self.output += str(msg) + "\n"
    try:
      self.output += str(msg) + "\n"
    except Exception as e:
      raise

  def call_allow_error(self, cmd):
    try:
      self.print_out("\n# Calling: " + cmd)
      out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
      return_code = 0
    except subprocess.CalledProcessError as e:
      return_code = e.returncode
      out = e.output
      self.output += "# ... call did not succeed"
      # return return_code, out
    except Exception as e:
      raise
    finally:
      new_output=out.decode("utf-8")
      self.output += new_output
      return return_code, new_output

  def call_no_error(self, cmd):
    return_code, out = self.call_allow_error(cmd)
    self.require(return_code == 0, "call failed: \"{0}\"".format(cmd))
    return out

  def run(self):
    localVars={
        # Meta info  about the test case
        "testcase_num":self.idx,
        "testcase_id": self.label,

        # Functions to execute processes
        "call": self.call_no_error,
        "call_may_fail": self.call_allow_error,

        # Other functions available to the test suite
        "uuid": self.get_uuid,
        "print":self.print_out,

        # Function to fail the test
        "fail": self.fail,
        "expect": self.expect,
        "abort": self.abort,
        "require": self.require,

        }

    status_message = ""
    print("==== Test case {:d}: \"{:s}\"".format(self.idx,self.label), end="")

    for stage_name, stage_spec in [("SETUP", self.setup), ("TEST", self.case), ("TEARDOWN", self.teardown)]:
      for spec_segment in stage_spec:
        try:
          self.print_out("\n### Test case {0}".format(stage_name))
          self.run_segment(spec_segment,localVars)
        except TestError:
          pass
        except Exception as e:
          self.record_failure("UNHANDLED EXCEPTION (check state: clean-up did not finish): {}".format(e), stage_name)
          break

    if len(self.case_failure) > 0:
      print(" FAILED ====================")
      for failure in self.case_failure:
        print("    {0} \"{1}\"".format(failure[0], failure[1]))
      print("    Output:")
      print(reindent(self.output, 4, "| ")+"\n")
    else:
      print(" PASSED ==============================")

    return len(self.case_failure) == 0

  def run_segment(self, spec_segment, localVars):
    if "code" in spec_segment:
      exec(spec_segment["code"],localVars)


class TestError(Exception):
  pass

# heavily adapted from from https://www.oreilly.com/library/view/python-cookbook/0596001673/ch03s12.html
def reindent(s, numSpaces, prompt):
    s = s.split('\n')
    s = [(numSpaces * ' ') + prompt + line for line in s]
    s = "\n".join(s)
    return s
