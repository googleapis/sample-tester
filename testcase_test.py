#!/usr/bin/env python3
import unittest
import test_suite

class TestTestCase(unittest.TestCase):
  def test_execute_valid_spec(self):
    success = test_suite.run([], ['testdata/testcase_passing.yaml'], [])
    self.assertTrue(success, "expected valid test file to pass")

if __name__ == '__main__':
    unittest.main()
