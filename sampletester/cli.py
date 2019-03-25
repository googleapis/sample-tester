#!/usr/bin/env python3
# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# See README.md for set-up instructions.

# Run all tests with:
#  python3 -m unittest discover -s . -p '*_test.py' -v
#
# Run examples by executing the `examples/**/run.sh` files; you can pass flags
# by setting FLAGS.
#
# You can run a quick verification that everything works (tests and all passing
# examples) by invoking the following (you can pass flags by setting FLAGS):
#   ./devcheck
#
#
# To find all TODOs:
#  grep -r TODO | grep -v '~' | grep -v /lib/


import argparse
import contextlib
import logging
import os
import string
import sys
import traceback

from sampletester import convention
from sampletester import environment_registry
from sampletester import runner
from sampletester import summary
from sampletester import testplan
from sampletester import xunit

VERSION = '0.9.0'
EXITCODE_SUCCESS = 0
EXITCODE_TEST_FAILURE = 1
EXITCODE_FLAG_ERROR = 2
EXITCODE_SETUP_ERROR = 3
EXITCODE_USER_ABORT = 4

DEFAULT_LOG_LEVEL = 100

# Set this to True to get a backtrace for debugging
DEBUGME=False

def main():
  args, usage = parse_cli()
  if not args:
    exit(EXITCODE_SETUP_ERROR)

  if args.version:
    print("sampletester version {}".format(VERSION))

  log_level = LOG_LEVELS[args.logging] or DEFAULT_LOG_LEVEL
  logging.basicConfig(level=log_level)
  logging.info("argv: {}".format(sys.argv))

  try:
    test_files, user_paths = get_files(args.files)

    registry = environment_registry.new(args.convention, user_paths)

    test_suites = testplan.suites_from(test_files, args.suites, args.cases)
    if len(test_suites) == 0:
      exit(EXITCODE_SUCCESS)
    manager = testplan.Manager(registry, test_suites, args.envs)
  except Exception as e:
    logging.error("fatal error: {}".format(repr(e)))
    print("\nERROR: could not run tests because {}\n".format(e))
    if DEBUGME:
      traceback.print_exc(file=sys.stdout)
    else:
      print(usage)
    exit(EXITCODE_SETUP_ERROR)

  verbosity = VERBOSITY_LEVELS[args.verbosity]
  quiet = verbosity == summary.Detail.NONE
  visitor = testplan.MultiVisitor(runner.Visitor(args.fail_fast),
                                  summary.SummaryVisitor(verbosity,
                                                         not args.suppress_failures,
                                                         debug=DEBUGME))
  try:
    success = manager.accept(visitor)
  except KeyboardInterrupt:
    print('\nkeyboard interrupt; aborting')
    exit(EXITCODE_USER_ABORT)

  if not quiet or (not success and not args.suppress_failures):
    print()
    if success:
      print("Tests passed")
    else:
      print("Tests failed")

  if args.xunit:
    try:
      with smart_open(args.xunit) as xunit_output:
        xunit_output.write(manager.accept(xunit.Visitor()))
      if not quiet:
        print('xUnit output written to "{}"'.format(args.xunit))
    except Exception as e:
      print("could not write xunit output to {}: {}".format(args.xunit, e))
      if DEBUGME:
        traceback.print_exc(file=sys.stdout)
      exit(EXITCODE_FLAG_ERROR)

  exit(EXITCODE_SUCCESS if success else EXITCODE_TEST_FAILURE)


LOG_LEVELS = {"none": None, "info": logging.INFO, "debug": logging.DEBUG}
DEFAULT_LOG_LEVEL = "none"

VERBOSITY_LEVELS = {"quiet": summary.Detail.NONE, "summary": summary.Detail.BRIEF, "detailed": summary.Detail.FULL}
DEFAULT_VERBOSITY_LEVEL = "summary"

def parse_cli():
  epilog = """CONFIGS consists of any number of the following, in any order:

  TEST.yaml files: these are the test plans to execute against the CONVENTION

  arbitrary files/paths, depending on CONVENTION. For `tag` (the
    default), these should be paths to `MANIFEST.manifest.yaml` files.
  """

  parser = argparse.ArgumentParser(
      description="A tool to run tests on equivalent samples in different languages",
      epilog=epilog,
      formatter_class=argparse.RawDescriptionHelpFormatter)

  parser.add_argument(
      "-c",
      "--convention",
      metavar="CONVENTION:ARG,ARG,...",
      help=('name of the convention to use in resolving artifact names in ' +
            'specific languages, and a comma-separated list of arguments to ' +
            'that convention (default: "{}")'.format(convention.DEFAULT)),
      default=convention.DEFAULT
  )

  parser.add_argument(
      "--xunit", metavar="FILE", help="xunit output file (use `-` for stdout)")

  parser.add_argument(
      "-v", "--verbosity",
      help=('how much output to show for passing tests (default: "{}")'
            .format(DEFAULT_VERBOSITY_LEVEL)),
      choices=list(VERBOSITY_LEVELS.keys()),
      default="summary"
      )

  parser.add_argument(
      "-f", "--suppress_failures",
      help="suppress showing output for failing cases",
      action='store_true')

  parser.add_argument(
      "-l",
      "--logging",
      help=('show logs at the specified level (default: "{}")'
            .format(DEFAULT_LOG_LEVEL)),
      choices=list(LOG_LEVELS.keys()),
      default="none")

  parser.add_argument(
      "--envs",
      metavar="TESTENV_FILTER",
      help="regex filtering test environments to execute"
  )

  parser.add_argument(
      "--suites",
      metavar="SUITE_FILTER",
      help="regex filtering test suites to execute"
  )

  parser.add_argument(
      "--cases",
      metavar="CASE_FILTER",
      help="regex filtering test cases to execute"
  )

  parser.add_argument(
      "--version",
      help="print version number",
      action="store_true")

  parser.add_argument(
      "--fail-fast",
      help=("stop execution as soon as any test case fails, preempting " +
            "additional test cases/suites/environments from running"),
      action="store_true")

  if len(sys.argv) == 1:
    parser.print_help()
    return None, None
  parser.add_argument("files", metavar="CONFIGS", nargs=argparse.REMAINDER)
  return parser.parse_args(), parser.format_usage()


# cf https://docs.python.org/3/library/argparse.html
def get_files(files):
  test_files = []
  user_paths = []
  for filename in files:
    filepath = os.path.abspath(filename)
    if os.path.isdir(filepath):
      user_paths.append(filepath)
      continue

    ext_split = os.path.splitext(filename)
    ext = ext_split[-1]
    if ext == ".yaml":
      prev_ext = os.path.splitext(ext_split[0])[-1]
      if prev_ext == ".manifest":
        user_paths.append(filepath)
      else:
        test_files.append(filepath)
    else:
      msg = 'unknown file type: "{}"'.format(filename)
      logging.critical(msg)
      raise ValueError(msg)
  return test_files, user_paths


# from https://stackoverflow.com/a/17603000
@contextlib.contextmanager
def smart_open(filename=None):
  if filename and filename != "-":
    fh = open(filename, "w")
  else:
    fh = sys.stdout

  try:
    yield fh
  finally:
    if fh is not sys.stdout:
      fh.close()


if __name__ == "__main__":
  main()
