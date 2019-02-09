#!/usr/bin/env python3

# pip install pyyaml

# https://docs.python.org/3/library/functions.html#exec
# https://pyyaml.org/wiki/PyYAMLDocumentation

# run with "manifest" convention (still need to change sample.manifest to a real manifest of the test samples; this fails at the moment because of that):
#  ./test_sample.py convention/manifest/ex.language.test.yaml convention/manifest/ex.language.manifest.yaml
#
# run with "cloud" convention:
#   ./test_sample.py convention/cloud/cloud.py convention/cloud/ex.language.test.yaml testdata/googleapis
#   ./test_sample.py convention/cloud/cloud.py convention/cloud/ex.product_search_test.yaml testdata/googleapis
#
#
# Run all tests:
#  python3 -m unittest discover -s . -p '*_test.py' -v
#
# Quick verification everything works:
#  python3 -m unittest discover -s . -p '*_test.py' -v && ./test_sample.py convention/manifest/ex.language.test.yaml convention/manifest/ex.language.manifest.yaml && echo -e "\n\nOK" || echo -e "\n\nERROR above"
#

import logging
import os
import string
import sys
import testenv
import runner
import convention
import testplan



usage_message = """\nUsage:
{} TEST.yaml [CONVENTION.py] [TEST.yaml ...] [USERPATH ...]

CONVENTION.py is one of `convention/manifest/id_by_region.py` (default) or
   `convention/cloud/cloud.py`

USERPATH depends on CONVENTION. For `id_by_region`, it should be a path to a
   `MANIFEST.manifest.yaml` file.
""".format(os.path.basename(__file__))

def main():
  logging.basicConfig(level=logging.INFO)
  logging.info("argv: {}".format(sys.argv))
  convention_files, test_files, user_paths = read_args(sys.argv)
  convention_files = convention_files or [convention.default]

  environment_registry = testenv.from_files(convention_files, user_paths)
  test_suites = testplan.suites_from(test_files)
  manager = testplan.Manager(environment_registry, test_suites)

  run_passed = manager.accept(runner.RunVisitor())

  if not run_passed:
    exit(-1)

# cf https://docs.python.org/3/library/argparse.html
def read_args(argv):
  convention_files = []
  test_files = []
  user_paths = []
  for filename in argv[1:]:
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
