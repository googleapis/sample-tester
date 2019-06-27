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
_ABS_DIR = os.path.dirname(_ABS_FILE)

class TestGenManifest(unittest.TestCase):

  def test_generation_v3_factored(self):
    self.maxDiff = None
    BIN = '/my/bin/'
    INVOCATION = 'call this way'
    CHDIR = '@/this/working/path/'
    ENV = 'python'

    gen_manifest_cwd = os.path.abspath(os.path.join(_ABS_DIR, '..', '..'))
    sample_relative_path = os.path.join('tests','testdata','gen_manifest')
    sample_path = os.path.abspath(os.path.join(gen_manifest_cwd, sample_relative_path))
    manifest_string = gen_manifest.emit_manifest_v3(
        tags = [('env', ENV),
                ('bin', BIN),
                ('invocation', INVOCATION),
                ('chdir', CHDIR)],
        sample_globs = [os.path.join(sample_relative_path, 'readbook.py'),
                        os.path.join(sample_relative_path, 'getbook.py')],
        flat = False)

    expected_string = """type: manifest/samples
schema_version: 3
base: &common
  env: '{env}'
  bin: '{bin}'
  invocation: '{invocation}'
  chdir: '{chdir}'
  basepath: '.'
samples:
- <<: *common
  path: '{{basepath}}/{sample_relative_path}/readbook.py'
  sample: 'readbook_sample'
- <<: *common
  path: '{{basepath}}/{sample_relative_path}/getbook.py'
  sample: 'getbook_sample'
""".format(env=ENV, bin=BIN, invocation=INVOCATION,
           chdir=CHDIR, sample_relative_path=sample_relative_path, cwd=gen_manifest_cwd)
    self.assertEqual(expected_string, manifest_string)

  def test_generation_v3_factored_basepath(self):
    self.maxDiff = None
    BIN = '/my/bin/'
    INVOCATION = 'call this way'
    CHDIR = '@/this/working/path/'
    ENV = 'python'
    BASEPATH = 'some/dir/path'

    gen_manifest_cwd = os.path.abspath(os.path.join(_ABS_DIR, '..', '..'))
    sample_relative_path = os.path.join('tests','testdata','gen_manifest')
    sample_path = os.path.abspath(os.path.join(gen_manifest_cwd, sample_relative_path))
    manifest_string = gen_manifest.emit_manifest_v3(
        tags = [('env', ENV),
                ('bin', BIN),
                ('invocation', INVOCATION),
                ('chdir', CHDIR),
                ('basepath', BASEPATH)],
        sample_globs = [os.path.join(sample_relative_path, 'readbook.py'),
                        os.path.join(sample_relative_path, 'getbook.py')],
        flat = False)

    expected_string = """type: manifest/samples
schema_version: 3
base: &common
  env: '{env}'
  bin: '{bin}'
  invocation: '{invocation}'
  chdir: '{chdir}'
  basepath: '{basepath}'
samples:
- <<: *common
  path: '{{basepath}}/{sample_relative_path}/readbook.py'
  sample: 'readbook_sample'
- <<: *common
  path: '{{basepath}}/{sample_relative_path}/getbook.py'
  sample: 'getbook_sample'
""".format(env=ENV, bin=BIN, invocation=INVOCATION,
           chdir=CHDIR, sample_relative_path=sample_relative_path, cwd=gen_manifest_cwd,
           basepath=BASEPATH)
    self.assertEqual(expected_string, manifest_string)

  def test_generation_v3_factored_forbidden_tag(self):
    self.maxDiff = None

    sample_path = os.path.abspath(os.path.join(_ABS_DIR, '..','testdata','gen_manifest'))
    for forbidden_name in ['path', 'sample']:
      with self.assertRaises(gen_manifest.TagNameError):
        manifest_string = gen_manifest.emit_manifest_v3(
            tags = [(forbidden_name, 'foo')],
            sample_globs = [os.path.join(sample_path, 'readbook.py'),
                            os.path.join(sample_path, 'getbook.py')],
            flat = False)

  def test_generation_v3_flat(self):
    self.maxDiff = None
    BIN = '/my/bin/'
    INVOCATION = 'call this way'
    CHDIR = '@/this/working/path/'
    ENV = 'python'

    gen_manifest_cwd = os.path.abspath(os.path.join(_ABS_DIR, '..', '..'))
    sample_relative_path = os.path.join('tests','testdata','gen_manifest')
    sample_path = os.path.abspath(os.path.join(gen_manifest_cwd, sample_relative_path))
    manifest_string = gen_manifest.emit_manifest_v3(
        tags = [('env', ENV),
                ('bin', BIN),
                ('invocation', INVOCATION),
                ('chdir', CHDIR),
                # ('basepath', 'should not be forbidden when flat')
        ],
        sample_globs = [os.path.join(sample_relative_path, 'readbook.py'),
                        os.path.join(sample_relative_path, 'getbook.py')],
        flat = True)

    expected_string = """type: manifest/samples
schema_version: 3
samples:
- bin: {bin}
  chdir: '{chdir}'
  env: {env}
  invocation: {invocation}
  path: ./{sample_relative_path}/readbook.py
  sample: readbook_sample
- bin: {bin}
  chdir: '{chdir}'
  env: {env}
  invocation: {invocation}
  path: ./{sample_relative_path}/getbook.py
  sample: getbook_sample
""".format(env=ENV, bin=BIN, invocation=INVOCATION, chdir=CHDIR, sample_relative_path=sample_relative_path)
    self.assertEqual(expected_string, manifest_string)

  def test_generation_v3_flat_basepath(self):
    self.maxDiff = None
    BIN = '/my/bin/'
    INVOCATION = 'call this way'
    CHDIR = '@/this/working/path/'
    ENV = 'python'
    BASEPATH = 'some/dir/path'

    gen_manifest_cwd = os.path.abspath(os.path.join(_ABS_DIR, '..', '..'))
    sample_relative_path = os.path.join('tests','testdata','gen_manifest')
    sample_path = os.path.abspath(os.path.join(gen_manifest_cwd, sample_relative_path))
    manifest_string = gen_manifest.emit_manifest_v3(
        tags = [('env', ENV),
                ('bin', BIN),
                ('invocation', INVOCATION),
                ('chdir', CHDIR),
                ('basepath', BASEPATH)],
        sample_globs = [os.path.join(sample_relative_path, 'readbook.py'),
                        os.path.join(sample_relative_path, 'getbook.py')],
        flat = True)

    expected_string = """type: manifest/samples
schema_version: 3
samples:
- bin: {bin}
  chdir: '{chdir}'
  env: {env}
  invocation: {invocation}
  path: {basepath}/{sample_relative_path}/readbook.py
  sample: readbook_sample
- bin: {bin}
  chdir: '{chdir}'
  env: {env}
  invocation: {invocation}
  path: {basepath}/{sample_relative_path}/getbook.py
  sample: getbook_sample
""".format(env=ENV, bin=BIN, invocation=INVOCATION, chdir=CHDIR, sample_relative_path=sample_relative_path,
           basepath=BASEPATH)
    self.assertEqual(expected_string, manifest_string)

  def test_generation_v3_flat_forbidden_tag(self):
    self.maxDiff = None

    sample_path = os.path.abspath(os.path.join(_ABS_DIR, '..','testdata','gen_manifest'))
    for forbidden_name in ['path', 'sample']:
      with self.assertRaises(gen_manifest.TagNameError):
        manifest_string = gen_manifest.emit_manifest_v3(
            tags = [(forbidden_name, 'foo')],
            sample_globs = [os.path.join(sample_path, 'readbook.py'),
                            os.path.join(sample_path, 'getbook.py')],
            flat = True)

  def test_generation_v2(self):
    self.maxDiff = None
    BIN = '/my/bin/'
    INVOCATION = 'call this way'
    CHDIR = '/this/working/path/'
    ENV = 'python'

    gen_manifest_cwd = os.path.abspath(os.path.join(_ABS_DIR, '..', '..'))
    sample_relative_path = os.path.join('tests','testdata','gen_manifest')
    sample_path = os.path.abspath(os.path.join(gen_manifest_cwd, sample_relative_path))
    manifest_string = gen_manifest.emit_manifest_v2(
        tags = [('env', ENV),
                ('bin', BIN),
                ('invocation', INVOCATION),
                ('chdir', CHDIR)],
        sample_globs = [os.path.join(sample_relative_path, 'readbook.py'),
                        os.path.join(sample_relative_path, 'getbook.py')],
        flat = False)

    expected_string = """version: 2
sets:
- environment: {env}
  bin: {bin}
  invocation: {invocation}
  chdir: {chdir}
  path: ./
  __items__:
  - path: {sample_relative_path}/readbook.py
    sample: readbook_sample
  - path: {sample_relative_path}/getbook.py
    sample: getbook_sample
""".format(env=ENV, bin=BIN, invocation=INVOCATION, chdir=CHDIR, cwd=gen_manifest_cwd,
           sample_relative_path=sample_relative_path)
    self.assertEqual(expected_string, manifest_string)

  def test_generation_v2_basepath(self):
    self.maxDiff = None
    BIN = '/my/bin/'
    INVOCATION = 'call this way'
    CHDIR = '/this/working/path/'
    ENV = 'python'
    BASEPATH = 'some/dir/path'


    gen_manifest_cwd = os.path.abspath(os.path.join(_ABS_DIR, '..', '..'))
    sample_relative_path = os.path.join('tests','testdata','gen_manifest')
    sample_path = os.path.abspath(os.path.join(gen_manifest_cwd, sample_relative_path))
    manifest_string = gen_manifest.emit_manifest_v2(
        tags = [('env', ENV),
                ('bin', BIN),
                ('invocation', INVOCATION),
                ('chdir', CHDIR),
                ('basepath', BASEPATH)],
        sample_globs = [os.path.join(sample_relative_path, 'readbook.py'),
                        os.path.join(sample_relative_path, 'getbook.py')],
        flat = False)

    expected_string = """version: 2
sets:
- environment: {env}
  bin: {bin}
  invocation: {invocation}
  chdir: {chdir}
  path: {basepath}/
  __items__:
  - path: {sample_relative_path}/readbook.py
    sample: readbook_sample
  - path: {sample_relative_path}/getbook.py
    sample: getbook_sample
""".format(env=ENV, bin=BIN, invocation=INVOCATION, chdir=CHDIR, cwd=gen_manifest_cwd,
           sample_relative_path=sample_relative_path,
           basepath=BASEPATH)
    self.assertEqual(expected_string, manifest_string)

  def test_generation_v2_factored_forbidden_tag(self):
    self.maxDiff = None

    sample_path = os.path.abspath(os.path.join(_ABS_DIR, '..','testdata','gen_manifest'))
    for forbidden_name in ['path', 'sample']:
      with self.assertRaises(gen_manifest.TagNameError):
        manifest_string = gen_manifest.emit_manifest_v2(
            tags = [(forbidden_name, 'foo')],
            sample_globs = [os.path.join(sample_path, 'readbook.py'),
                            os.path.join(sample_path, 'getbook.py')],
            flat = False)
