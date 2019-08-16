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

import os
import unittest

from contextlib import contextmanager

from sampletester import parser

_ABS_FILE = os.path.abspath(__file__)
_ABS_DIR = os.path.dirname(_ABS_FILE)

class TestParser(unittest.TestCase):
  def test_only_files_in(self):
    with pushd(os.path.join(_ABS_DIR, 'testdata', 'inputs')):
      self.assertEquals(set(), parser.only_files_in({'configs'}))
      self.assertEquals({'configs/zebra_m.yaml'},
                        parser.only_files_in({'configs', 'configs/zebra_m.yaml'}))
      self.assertEquals({'configs/zebra_m.yaml'},
                        parser.only_files_in({'configs/zebra_m.yaml'}))



@contextmanager
def pushd(new_dir):
  """A contextmanager that scopes being in a specified dir (like pushd)"""
  previous_dir = os.getcwd()
  os.chdir(new_dir)
  try:
    yield
  finally:
    os.chdir(previous_dir)
