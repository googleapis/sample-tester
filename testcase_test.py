#!/usr/bin/env python3
import unittest
import runner
import os
import convention
import testenv

class TestTestCase(unittest.TestCase):
  def setUp(self):
    __abs_file__ = os.path.abspath(__file__)
    self.__abs_file_path__ = os.path.split(__abs_file__)[0]
    self.environment_registry = testenv.from_files([convention.default], [])

  def pathTo(self, dir):
    return os.path.join(self.__abs_file_path__, dir)

  def test_passing(self):
    success = runner.run(self.environment_registry, [self.pathTo('testdata/testcase_passing.yaml')])
    self.assertTrue(success, "expected valid test file to pass")

if __name__ == '__main__':
    unittest.main()
