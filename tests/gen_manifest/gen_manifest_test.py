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

from glob import glob
import unittest
import os

from click.testing import CliRunner
from collections import OrderedDict
from gen_manifest import gen_manifest
from textwrap import dedent

_ABS_FILE = os.path.abspath(__file__)
_ABS_DIR = os.path.dirname(_ABS_FILE)

class TestGenManifest(unittest.TestCase):

  def test_glob_non_yaml(self):
    def basenames_of(files):
      return {os.path.basename(match) for match in files}

    gen_manifest_cwd = os.path.abspath(os.path.join(_ABS_DIR, '..', '..'))
    sample_relative_path = os.path.join('tests','testdata','gen_manifest')
    sample_path = os.path.abspath(os.path.join(gen_manifest_cwd, sample_relative_path))
    self.assertEquals({'readbook.py', 'getbook.py', 'some.random.yaml'},
                      basenames_of(
                          glob(os.path.join(sample_path, '**/*'),
                               recursive=True)))

    # ensure we exclude the *.yaml incldued in the naive globbing above
    self.assertEquals({'readbook.py', 'getbook.py'},
                      basenames_of(
                          gen_manifest.glob_non_yaml(
                              os.path.join(sample_path, '**/*'))))

  def test_parse_files_and_tags(self):
    files, tags = gen_manifest.parse_files_and_tags(['--principal=alice',
                                                     'crypto/path/scenario',
                                                     '--respondent=bob',
                                                     '/doc/sample'])
    self.assertEqual(['/doc/sample', 'crypto/path/scenario'], files)
    self.assertEqual([('principal', 'alice'), ('respondent', 'bob')], tags)

  def test_generation_v3_factored(self):
    self.maxDiff = None
    BIN = '/my/bin/'
    INVOCATION = 'call this way'
    CHDIR = '@/this/working/path/'
    ENVIRONMENT = 'python'

    gen_manifest_cwd = os.path.abspath(os.path.join(_ABS_DIR, '..', '..'))
    sample_relative_path = os.path.join('tests','testdata','gen_manifest')
    sample_path = os.path.abspath(os.path.join(gen_manifest_cwd, sample_relative_path))
    manifest_string = gen_manifest.emit_manifest_v3(
        tags = [('environment', ENVIRONMENT),
                ('bin', BIN),
                ('invocation', INVOCATION),
                ('chdir', CHDIR)],
        sample_globs = [os.path.join(sample_relative_path, 'readbook.py'),
                        os.path.join(sample_relative_path, 'getbook.py')],
        flat = False)

    expected_string = dedent(f"""\
      type: manifest/samples
      schema_version: 3
      base: &common
        environment: '{ENVIRONMENT}'
        bin: '{BIN}'
        invocation: '{INVOCATION}'
        chdir: '{CHDIR}'
        basepath: '.'
      samples:
      - <<: *common
        path: '{{basepath}}/{sample_relative_path}/readbook.py'
        sample: 'readbook_sample'
      - <<: *common
        path: '{{basepath}}/{sample_relative_path}/getbook.py'
        sample: 'getbook_sample'
      """)
    self.assertEqual(expected_string, manifest_string)

  def test_generation_v3_factored_globbed(self):
    self.maxDiff = None
    BIN = '/my/bin/'
    INVOCATION = 'call this way'
    CHDIR = '@/this/working/path/'
    ENVIRONMENT = 'python'

    gen_manifest_cwd = os.path.abspath(os.path.join(_ABS_DIR, '..', '..'))
    sample_relative_path = os.path.join('tests','testdata','gen_manifest')
    sample_path = os.path.abspath(os.path.join(gen_manifest_cwd, sample_relative_path))
    manifest_string = gen_manifest.emit_manifest_v3(
        tags = [('environment', ENVIRONMENT),
                ('bin', BIN),
                ('invocation', INVOCATION),
                ('chdir', CHDIR)],
        sample_globs = [os.path.join(sample_relative_path, '**/*')],
        flat = False)

    expected_string = dedent(f"""\
      type: manifest/samples
      schema_version: 3
      base: &common
        environment: '{ENVIRONMENT}'
        bin: '{BIN}'
        invocation: '{INVOCATION}'
        chdir: '{CHDIR}'
        basepath: '.'
      samples:
      - <<: *common
        path: '{{basepath}}/{sample_relative_path}/readbook.py'
        sample: 'readbook_sample'
      - <<: *common
        path: '{{basepath}}/{sample_relative_path}/getbook.py'
        sample: 'getbook_sample'
      """)
    self.assertEqual(expected_string, manifest_string)

  def test_generation_v3_factored_cli(self):
    self.maxDiff = None
    BIN = '/my/bin/'
    INVOCATION = 'call this way'
    CHDIR = '@/this/working/path/'
    ENVIRONMENT = 'python'

    gen_manifest_cwd = os.path.abspath(os.path.join(_ABS_DIR, '..', '..'))
    sample_relative_path = os.path.join('tests','testdata','gen_manifest')
    sample_path = os.path.abspath(os.path.join(gen_manifest_cwd, sample_relative_path))

    runner = CliRunner()
    result = runner.invoke(
        gen_manifest.main,
        ['--schema_version=3',
         f'--environment={ENVIRONMENT}',
         f'--bin={BIN}',
         f'--invocation={INVOCATION}',
         f'--chdir={CHDIR}',
         f'{os.path.join(sample_relative_path, "readbook.py")}',
         f'{os.path.join(sample_relative_path, "getbook.py")}'])

    expected_string = dedent(f"""\
      type: manifest/samples
      schema_version: 3
      base: &common
        environment: '{ENVIRONMENT}'
        bin: '{BIN}'
        invocation: '{INVOCATION}'
        chdir: '{CHDIR}'
        basepath: '.'
      samples:
      - <<: *common
        path: '{{basepath}}/{sample_relative_path}/getbook.py'
        sample: 'getbook_sample'
      - <<: *common
        path: '{{basepath}}/{sample_relative_path}/readbook.py'
        sample: 'readbook_sample'
      """)

    self.assertEqual(0, result.exit_code)
    self.assertEqual(expected_string, result.output)


  def test_generation_v3_factored_basepath(self):
    self.maxDiff = None
    BIN = '/my/bin/exe --flag'
    INVOCATION = 'call this way'
    CHDIR = '@/this/working/path/'
    ENVIRONMENT = 'python'
    BASEPATH = 'some/dir/path'

    gen_manifest_cwd = os.path.abspath(os.path.join(_ABS_DIR, '..', '..'))
    sample_relative_path = os.path.join('tests','testdata','gen_manifest')
    sample_path = os.path.abspath(os.path.join(gen_manifest_cwd, sample_relative_path))
    manifest_string = gen_manifest.emit_manifest_v3(
        tags = [('environment', ENVIRONMENT),
                ('bin', BIN),
                ('invocation', INVOCATION),
                ('chdir', CHDIR),
                ('basepath', BASEPATH)],
        sample_globs = [os.path.join(sample_relative_path, 'readbook.py'),
                        os.path.join(sample_relative_path, 'getbook.py')],
        flat = False)

    expected_string = dedent(f"""\
      type: manifest/samples
      schema_version: 3
      base: &common
        environment: '{ENVIRONMENT}'
        bin: '{BIN}'
        invocation: '{INVOCATION}'
        chdir: '{CHDIR}'
        basepath: '{BASEPATH}'
      samples:
      - <<: *common
        path: '{{basepath}}/{sample_relative_path}/readbook.py'
        sample: 'readbook_sample'
      - <<: *common
        path: '{{basepath}}/{sample_relative_path}/getbook.py'
        sample: 'getbook_sample'
      """)
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
    ENVIRONMENT = 'python'

    gen_manifest_cwd = os.path.abspath(os.path.join(_ABS_DIR, '..', '..'))
    sample_relative_path = os.path.join('tests','testdata','gen_manifest')
    sample_path = os.path.abspath(os.path.join(gen_manifest_cwd, sample_relative_path))
    manifest_string = gen_manifest.emit_manifest_v3(
        tags = [('environment', ENVIRONMENT),
                ('bin', BIN),
                ('invocation', INVOCATION),
                ('chdir', CHDIR),
        ],
        sample_globs = [os.path.join(sample_relative_path, 'readbook.py'),
                        os.path.join(sample_relative_path, 'getbook.py')],
        flat = True)

    expected_string = dedent(f"""\
      type: manifest/samples
      schema_version: 3
      samples:
      - path: './{sample_relative_path}/readbook.py'
        sample: 'readbook_sample'
        environment: '{ENVIRONMENT}'
        bin: '{BIN}'
        invocation: '{INVOCATION}'
        chdir: '{CHDIR}'
      - path: './{sample_relative_path}/getbook.py'
        sample: 'getbook_sample'
        environment: '{ENVIRONMENT}'
        bin: '{BIN}'
        invocation: '{INVOCATION}'
        chdir: '{CHDIR}'
      """)
    self.assertEqual(expected_string, manifest_string)

  def test_generation_v3_flat_basepath(self):
    self.maxDiff = None
    BIN = '/my/bin/'
    INVOCATION = 'call this way'
    CHDIR = '@/this/working/path/'
    ENVIRONMENT = 'python'
    BASEPATH = 'some/dir/path'

    gen_manifest_cwd = os.path.abspath(os.path.join(_ABS_DIR, '..', '..'))
    sample_relative_path = os.path.join('tests','testdata','gen_manifest')
    sample_path = os.path.abspath(os.path.join(gen_manifest_cwd, sample_relative_path))
    manifest_string = gen_manifest.emit_manifest_v3(
        tags = [('environment', ENVIRONMENT),
                ('bin', BIN),
                ('invocation', INVOCATION),
                ('chdir', CHDIR),
                ('basepath', BASEPATH)],
        sample_globs = [os.path.join(sample_relative_path, 'readbook.py'),
                        os.path.join(sample_relative_path, 'getbook.py')],
        flat = True)

    expected_string = dedent(f"""\
      type: manifest/samples
      schema_version: 3
      samples:
      - path: '{BASEPATH}/{sample_relative_path}/readbook.py'
        sample: 'readbook_sample'
        environment: '{ENVIRONMENT}'
        bin: '{BIN}'
        invocation: '{INVOCATION}'
        chdir: '{CHDIR}'
      - path: '{BASEPATH}/{sample_relative_path}/getbook.py'
        sample: 'getbook_sample'
        environment: '{ENVIRONMENT}'
        bin: '{BIN}'
        invocation: '{INVOCATION}'
        chdir: '{CHDIR}'
      """)
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
    ENVIRONMENT = 'python'

    gen_manifest_cwd = os.path.abspath(os.path.join(_ABS_DIR, '..', '..'))
    sample_relative_path = os.path.join('tests','testdata','gen_manifest')
    sample_path = os.path.abspath(os.path.join(gen_manifest_cwd, sample_relative_path))
    manifest_string = gen_manifest.emit_manifest_v2(
        tags = [('env', ENVIRONMENT),
                ('bin', BIN),
                ('invocation', INVOCATION),
                ('chdir', CHDIR)],
        sample_globs = [os.path.join(sample_relative_path, 'readbook.py'),
                        os.path.join(sample_relative_path, 'getbook.py')],
        flat = False)

    expected_string = dedent(f"""\
      version: 2
      sets:
      - environment: {ENVIRONMENT}
        bin: {BIN}
        invocation: {INVOCATION}
        chdir: {CHDIR}
        path: ./
        __items__:
        - path: {sample_relative_path}/readbook.py
          sample: readbook_sample
        - path: {sample_relative_path}/getbook.py
          sample: getbook_sample
      """)
    self.assertEqual(expected_string, manifest_string)

  def test_generation_v2_basepath(self):
    self.maxDiff = None
    BIN = '/my/bin/'
    INVOCATION = 'call this way'
    CHDIR = '/this/working/path/'
    ENVIRONMENT = 'python'
    BASEPATH = 'some/dir/path'


    gen_manifest_cwd = os.path.abspath(os.path.join(_ABS_DIR, '..', '..'))
    sample_relative_path = os.path.join('tests','testdata','gen_manifest')
    sample_path = os.path.abspath(os.path.join(gen_manifest_cwd, sample_relative_path))
    manifest_string = gen_manifest.emit_manifest_v2(
        tags = [('env', ENVIRONMENT),
                ('bin', BIN),
                ('invocation', INVOCATION),
                ('chdir', CHDIR),
                ('basepath', BASEPATH)],
        sample_globs = [os.path.join(sample_relative_path, 'readbook.py'),
                        os.path.join(sample_relative_path, 'getbook.py')],
        flat = False)

    expected_string = dedent(f"""\
      version: 2
      sets:
      - environment: {ENVIRONMENT}
        bin: {BIN}
        invocation: {INVOCATION}
        chdir: {CHDIR}
        path: {BASEPATH}/
        __items__:
        - path: {sample_relative_path}/readbook.py
          sample: readbook_sample
        - path: {sample_relative_path}/getbook.py
          sample: getbook_sample
      """)
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
