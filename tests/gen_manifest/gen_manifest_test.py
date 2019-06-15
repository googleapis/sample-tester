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

import unittest
import os

from collections import OrderedDict
from gen_manifest import gen_manifest

_ABS_FILE = os.path.abspath(__file__)
_ABS_DIR = os.path.split(_ABS_FILE)[0]

class TestGenManifest(unittest.TestCase):

  def test_generation_v2(self):
    self.maxDiff = None
    BIN = '/my/bin/'
    INVOCATION = 'call this way'
    CHDIR = '/this/working/path/'
    ENV = 'python'

    gen_manifest_cwd = os.path.abspath(os.path.join(_ABS_DIR, '..', '..'))
    sample_path = os.path.abspath(os.path.join(_ABS_DIR, '..','testdata','gen_manifest'))
    manifest = gen_manifest.create_manifest_v2(labels = [('env', ENV),
                                                         ('bin', BIN),
                                                         ('invocation', INVOCATION),
                                                         ('chdir', CHDIR)],
                                               samples = [os.path.join(sample_path, '*.py')])
    manifest_string = gen_manifest.dump(manifest)

    expected_string = """version: 2
sets:
- environment: {}
  bin: {}
  invocation: {}
  chdir: {}
  path: {}/
  __items__:
  - path: {}/readbook.py
    sample: readbook_sample
  - path: {}/getbook.py
    sample: getbook_sample
""".format(ENV, BIN, INVOCATION, CHDIR, gen_manifest_cwd,
           sample_path, sample_path)
    self.assertEquals(expected_string, manifest_string)
