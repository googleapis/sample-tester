#!/usr/bin/env python3

# pip install pyyaml

# https://docs.python.org/3/library/functions.html#exec
# https://pyyaml.org/wiki/PyYAMLDocumentation

# run with "manifest" convention (still need to change sample.manifest to a real manifest of the test samples; this fails at the moment because of that):
#  ./test_sample.py convention/manifest/ex.language.test.yaml convention/manifest/ex.language.manifest.yaml
#
# run with "cloud" convention:
#   # a passing test:
#   ./test_sample.py convention/cloud/cloud.py convention/cloud/ex.language.test.yaml testdata/googleapis
#   # a failing test:
#   ./test_sample.py convention/cloud/cloud.py convention/cloud/ex.product_search_test.yaml testdata/googleapis
#
#
# Run all tests:
#  python3 -m unittest discover -s . -p '*_test.py' -v
#
# Quick verification everything works:
#  FLAGS="--xunit FOO -s -v"; python3 -m unittest discover -s . -p '*_test.py' -v && ./test_sample.py $FLAGS convention/manifest/ex.language.test.yaml convention/manifest/ex.language.manifest.yaml && ./test_sample.py $FLAGS convention/cloud/cloud.py convention/cloud/ex.language.test.yaml testdata/googleapis && echo -e "\n\nOK" || echo -e "\n\nERROR above"
#

import logging
import os
import string
import sys
import testenv
import runner
import convention
import testplan
import summary
import xunit
import argparse


usage_message = """\nUsage:
{} TEST.yaml [CONVENTION.py] [TEST.yaml ...] [USERPATH ...]

CONVENTION.py is one of `convention/manifest/id_by_region.py` (default) or
   `convention/cloud/cloud.py`

USERPATH depends on CONVENTION. For `id_by_region`, it should be a path to a
   `MANIFEST.manifest.yaml` file.
""".format(os.path.basename(__file__))

def main():
  args = parse_cli()

  log_level=LOG_LEVELS[args.logging]
  if log_level is not None:
    logging.basicConfig(level=log_level)
  logging.info("argv: {}".format(sys.argv))

  convention_files, test_files, user_paths = get_files(args.files)
  convention_files = convention_files or [convention.default]

  environment_registry = testenv.from_files(convention_files, user_paths)
  test_suites = testplan.suites_from(test_files)
  manager = testplan.Manager(environment_registry, test_suites)

  run_passed = manager.accept(runner.RunVisitor())

  if args.summary:
    print(manager.accept(summary.SummaryVisitor(args.verbose)))
    print()

  if args.xunit:
    print(manager.accept(xunit.XUnitVisitor()))
    print()

  if not run_passed:
    print('Tests failed')
    exit(-1)
  print('Tests passed')


LOG_LEVELS = {
    "none": None,
    "info": logging.INFO,
    "debug": logging.DEBUG
}

def parse_cli():
  parser = argparse.ArgumentParser(description="A tool to run tests on equivalent samples in different languages")
  parser.add_argument("--xunit", metavar='FILE', help="xunit output file")
  parser.add_argument("-s", "--summary", help="show test status summary on stdout", action="store_true")
  parser.add_argument("-v", "--verbose", help="if -s, be verbose", action="store_true")
  parser.add_argument("-l", "--logging", metavar='LEVEL', help="show logs at the specified level", choices=list(LOG_LEVELS.keys()), default="none")

  parser.add_argument('files', nargs=argparse.REMAINDER)
  return  parser.parse_args()


# cf https://docs.python.org/3/library/argparse.html
def get_files(files):
  convention_files = []
  test_files = []
  user_paths = []
  for filename in files:
    filepath = os.path.abspath(filename)
    if os.path.isdir(filepath):
      user_paths.append(filepath)
      continue

    ext_split = os.path.splitext(filename)
    ext = ext_split[-1]
    if ext == ".py":
      convention_files.append(filepath)
    elif ext == ".yaml":
      prev_ext = os.path.splitext(ext_split[0])[-1]
      if prev_ext == ".manifest":
        user_paths.append(filepath)
      else:
        test_files.append(filepath)
    else:
      msg = 'unknown file type: "{}"\n{}'.format(filename, usage_message)
      logging.critical(msg)
      raise ValueError(msg)
  return convention_files, test_files, user_paths


#  eval(spec["test"]["case"])

if __name__== "__main__":
  main()
