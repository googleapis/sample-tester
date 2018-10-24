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

    self.last_return_code = 0
    self.last_call_output = ""

    self.localVars={
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


  def get_uuid(self):
    return str(uuid.uuid4())

  def record_failure(self, status, message, *args):
    self.case_failure.append((status,message))

  def expect(self, condition, message, *args):
    if not condition:
      self.record_failure("FAILED EXPECTATION", message, *args)

  def fail(self):
    self.expect(False, "failure")

  def require(self, condition, message, *args):
    if not condition:
      self.record_failure("FAILED REQUIREMENT", message, *args)
      raise TestError

  def abort(self):
    self.require(False, "abort called")

  def print_out(self, msg, *args):
    #    self.output += str(msg) + "\n"
    try:
      self.output += self.format_string(str(msg), *args) + "\n"
    except Exception as e:
      raise

  # helper
  def format_string(self, msg, *args):
    if len(args) == 0:
      return msg
    count = msg.count("{}")
    missing = len(args) - count
    if missing > 0:
      msg = msg + ": " + "{} "*missing
    formatted = msg.format(*args)
    return formatted

  def call_allow_error(self, cmd, *args):
    self.last_return_code = 0
    self.last_call_output = ""

    cmd = self.format_string(cmd, *args)
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
      self.last_return_code = return_code
      self.last_call_output = new_output
      self.output += new_output
      return return_code, new_output

  def call_no_error(self, cmd, *args):
    return_code, out = self.call_allow_error(cmd, *args)
    self.require(return_code == 0, "call failed: \"{0}\"".format(cmd))
    return out

  def last_output_contains(self, substr):
    return substr in self.last_call_output

  def expect_contains(self, *values):
    for substr in values:
      self.expect(self.last_output_contains(substr), 'expected "{}" present in preceding output'.format(substr))

  def require_contains(self, *values):
    for substr in values:
      self.require(self.last_output_contains(substr), 'required "{}" present in preceding output'.format(substr))

  def expect_not_contains(self, *values):
    for substr in values:
      self.expect(not self.last_output_contains(substr), 'expected "{}" absent in preceding output'.format(substr))

  def require_not_contains(self, *values):
    for substr in values:
      self.require(not self.last_output_contains(substr), 'required "{}" absent in preceding output'.format(substr))

  def run(self):

    status_message = ""
    print("---- Test case {:d}: \"{:s}\"".format(self.idx,self.label), end="")

    for stage_name, stage_spec in [("SETUP", self.setup), ("TEST", self.case), ("TEARDOWN", self.teardown)]:
      self.print_out("\n### Test case {0}".format(stage_name))
      for spec_segment in stage_spec:
        try:
          self.run_segment(spec_segment)
        except TestError:
          pass
        except Exception as e:
          self.record_failure("UNHANDLED EXCEPTION (check state: clean-up did not finish): {}".format(e), stage_name)
          break

    print_output = True
    if len(self.case_failure) > 0:
      print(" FAILED --------------------")
      for failure in self.case_failure:
        print("    {0} \"{1}\"".format(failure[0], failure[1]))
        print_output = True
    else:
      print(" PASSED ------------------------------")
    if print_output:
      print("    Output:")
      print(reindent(self.output, 4, "| ")+"\n")

    return len(self.case_failure) == 0

  def run_segment(self, spec_segment):
    if len(spec_segment) > 1:
      raise ConfigError

    # Make everything below into a lookup table
    if "code" in spec_segment:
      exec(spec_segment["code"], self.localVars)
    if "uuid" in spec_segment:
      var_name = spec_segment["uuid"]
      self.localVars[var_name] = self.get_uuid()
    if "print" in spec_segment:
      parts = spec_segment["print"]
      self.print_out(self.args_to_string(parts))
    if "call_may_fail" in spec_segment:
      parts = spec_segment["call_may_fail"]
      self.call_allow_error(parts[0], *(self.lookup_values(parts[1:])))
    if "call" in spec_segment:
      parts = spec_segment["call"]
      self.call_no_error(parts[0], *(self.lookup_values(parts[1:])))
    if "require_not_contains" in spec_segment:
      items = spec_segment["require_not_contains"]
      self.require_not_contains(*self.get_yaml_values(items))

  def get_yaml_values(self, list):
    values = []
    for type, item in enumerate(list):
      if type == "symbol":
        item = self.localVars[item]
      values.append(item)
    return values

  def lookup_values(self, variables):
    return [self.localVars[p] for p in variables]

  def args_to_string(self, parts):
    if len(parts) == 0:
      return ""
    if len(parts) == 1:
      return parts[0]
    if len(parts) > 1:
      return parts[0].format(*[self.localVars[p] for p in parts[1:]])

class TestError(Exception):
  pass

class ConfigError(Exception):
  pass

# heavily adapted from from https://www.oreilly.com/library/view/python-cookbook/0596001673/ch03s12.html
def reindent(s, numSpaces, prompt):
    s = s.split('\n')
    s = [(numSpaces * ' ') + prompt + line for line in s]
    s = "\n".join(s)
    return s
