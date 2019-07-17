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

from typing import Dict
from typing import List
from typing import Tuple

from sampletester import convention
from sampletester import environment_registry
from sampletester import parser
from sampletester import runner
from sampletester import summary
from sampletester import testplan
from sampletester import xunit

from sampletester.sample_manifest import SCHEMA_TYPE_VALUE as MANIFEST_TYPE
from sampletester.testplan import SCHEMA_TYPE_VALUE as TESTPLAN_TYPE

VERSION = '0.15.3'
EXITCODE_SUCCESS = 0
EXITCODE_TEST_FAILURE = 1
EXITCODE_FLAG_ERROR = 2
EXITCODE_SETUP_ERROR = 3
EXITCODE_USER_ABORT = 4

DEFAULT_LOG_LEVEL = 100

# Set this to True to get a backtrace for debugging
DEBUGME=True

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

    all_docs = parser.from_files(*args.files)
    # TODO NEXT:
    # - make from_files, from_string be methods on IndexedDocs
    # - then call that directly instead of the above (with the resolver I put at the bottom of this file to pick up old-style files)
    # - then get rid of sort_docs in favor of passing the whole IndexedDocs to testplan, and it can get the files of the type it needs


    test_docs, manifest_docs = sort_docs(parser.from_files(*args.files))

    # TODO: Remove the following temporary lines once we pass the parsed
    # objects to the other modules, instead of the filenames
    # >>>>
    #  DONE  test_files =  [doc.path for doc in test_docs]
    user_paths =  [doc.path for doc in manifest_docs]
    # user_paths =  [doc.path for doc in all_docs.of_type()]
    # <<<<


    registry = environment_registry.new(args.convention, user_paths)

    test_suites = testplan.suites_from_doc_list(test_docs, args.suites, args.cases)  ###
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

def sort_docs(docs: Dict[str,
                         List[parser.Document]]) -> Tuple[List[parser.Document],
                                                          List[parser.Document]]:
  """Returns separate lists of testplan and manifest YAML docs.

  This function separates the manifest and testplan documents into two separate
  lists. For documents of unknown type (parser.SCHEMA_TYPE_ABSENT), it employs
  the filename to assign to one of those two lists: documents with paths ending
  in "manifest.yaml" are considered manifests, and any remaining documents iwth
  paths ending in ".yaml" are considered testplans.

  Args:
    docs: A dictionary of YAML type values to a list of parser.Document. Each
      such Document describes a YAML document.

  Returns: A list with testplan documents, and a list with manifest
    documents. Each of these documents is represented by a parser.Document, so it
    includes the parsed content and either the filepath or a description.
  """
  manifest_docs = docs.get(MANIFEST_TYPE,[])
  testplan_docs = docs.get(TESTPLAN_TYPE,[])

  for unknown_doc in docs.get(parser.SCHEMA_TYPE_ABSENT):
    ext_split = os.path.splitext(unknown_doc.path)
    ext = ext_split[-1]
    if ext == ".yaml":
      prev_ext = os.path.splitext(ext_split[0])[-1]
      if prev_ext == ".manifest":
        manifest_docs.append(unknown_doc)
      else:
        testplan_docs.append(unknown_doc)
    else:
      msg = 'unknown file type: "{}"'.format(unknown_doc.path)
      logging.critical(msg)
      raise ValueError(msg)

  return testplan_docs, manifest_docs

def resolver(unknown_doc) -> str :
  ext_split = os.path.splitext(unknown_doc.path)
  ext = ext_split[-1]
  if ext == ".yaml":
    prev_ext = os.path.splitext(ext_split[0])[-1]
    if prev_ext == ".manifest":
      return MANIFEST_TYPE
    else:
      return TESTPLAN_TYPE
  else:
    msg = 'unknown file type: "{}"'.format(unknown_doc.path)
    logging.critical(msg)
    raise ValueError(msg)





if __name__ == "__main__":
  main()
