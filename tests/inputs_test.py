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

from sampletester import inputs
from sampletester import parser

_ABS_FILE = os.path.abspath(__file__)
_ABS_DIR = os.path.dirname(_ABS_FILE)

class TestInputs(unittest.TestCase):
  def test_untyped_yaml_resolver(self):
    self.assertEquals(inputs.MANIFEST_SCHEMA.primary_type,
                      inputs.untyped_yaml_resolver(
                          parser.Document('/my/path/to/some.manifest.yaml', None)))
    self.assertEquals(inputs.TESTPLAN_SCHEMA.primary_type,
                      inputs.untyped_yaml_resolver(
                          parser.Document('path/to/some.yaml', None)))
    self.assertEquals(inputs.UNKNOWN_TYPE,
                      inputs.untyped_yaml_resolver(
                          parser.Document('path/to/some.txt', None)))

  def test_get_globbed(self):
    with pushd(os.path.join(_ABS_DIR, 'testdata', 'inputs')):
      self.assertEquals(set(), inputs.get_globbed())
      self.assertEquals(set(), inputs.get_globbed(''))
      self.assertEquals({'alternate-configs', 'configs', 'data', 'multidocs'},
                        inputs.get_globbed('*'))
      self.assertEquals({'configs/vicuna_t.yaml',
                         'configs/some.yaml',
                         'configs/some.txt',
                         'alternate-configs/vicuna_t.yaml',
                         'alternate-configs/some.yaml',
                         'alternate-configs/some.txt'},
                        inputs.get_globbed('**/some*', '**/vicuna*'))
      self.assertEquals({'configs',
                         'configs/zebra_m.yaml',
                         'configs/yak_m.yaml',
                         'configs/woodchuck_t.yaml',
                         'configs/vicuna_t.yaml',
                         'configs/some.yaml',
                         'configs/other.yaml',
                         'configs/some.txt',
                         'alternate-configs',
                         'alternate-configs/zebra_m.yaml',
                         'alternate-configs/yak_m.yaml',
                         'alternate-configs/woodchuck_t.yaml',
                         'alternate-configs/vicuna_t.yaml',
                         'alternate-configs/some.yaml',
                         'alternate-configs/other.yaml',
                         'alternate-configs/some.txt',
                         'data',
                         'data/datafile.txt',
                         'multidocs',
                         'multidocs/mosquito.yaml',
                         'multidocs/bee.yaml',
                         'multidocs/ant.yaml',
                         'multidocs/ant.manifest.yaml' },
                        inputs.get_globbed('**/*'))
      self.assertEquals({'configs/zebra_m.yaml',
                         'configs/yak_m.yaml',
                         'alternate-configs/zebra_m.yaml',
                         'alternate-configs/yak_m.yaml'},
                        inputs.get_globbed('**/*_m*'))

  def test_index_docs_configs(self):
    with pushd(os.path.join(_ABS_DIR, 'testdata', 'inputs')):
      indexed = inputs.index_docs('configs/*.yaml')
      self.assertEquals({os.path.abspath(fname) for fname in
                         {'configs/zebra_m.yaml',
                          'configs/yak_m.yaml'}},
                        {doc.path
                         for doc in indexed.of_type(inputs.MANIFEST_SCHEMA.primary_type)})
      self.assertEquals({os.path.abspath(fname) for fname in
                         {'configs/woodchuck_t.yaml',
                          'configs/vicuna_t.yaml',
                          'configs/some.yaml'}},
                        {doc.path
                         for doc in indexed.of_type(inputs.TESTPLAN_SCHEMA.primary_type)})
      self.assertEquals(set(),
                        {doc.path
                         for doc in indexed.of_type(parser.SCHEMA_TYPE_ABSENT)})

  def test_index_docs_implicit(self):
    with pushd(os.path.join(_ABS_DIR, 'testdata', 'inputs')):
      # All files are configs.
      indexed = inputs.index_docs()
      self.assertEquals({os.path.abspath(fname) for fname in
                         {'configs/zebra_m.yaml',
                          'configs/yak_m.yaml',
                          'alternate-configs/zebra_m.yaml',
                          'alternate-configs/yak_m.yaml',
                          'multidocs/bee.yaml',
                          'multidocs/mosquito.yaml',
                          'multidocs/ant.manifest.yaml'}},
                        {doc.path
                         for doc in indexed.of_type(inputs.MANIFEST_SCHEMA.primary_type)})
      self.assertEquals({os.path.abspath(fname) for fname in
                         {'configs/woodchuck_t.yaml',
                          'configs/vicuna_t.yaml',
                          'configs/some.yaml',
                          'alternate-configs/woodchuck_t.yaml',
                          'alternate-configs/vicuna_t.yaml',
                          'alternate-configs/some.yaml',
                          'multidocs/bee.yaml',
                          'multidocs/mosquito.yaml',
                          'multidocs/ant.yaml'}},
                        {doc.path
                         for doc in indexed.of_type(inputs.TESTPLAN_SCHEMA.primary_type)})
      self.assertEquals(set(),
                        {doc.path
                         for doc in indexed.of_type(parser.SCHEMA_TYPE_ABSENT)})

      # Explicitly specify a manifest file (only 1):
      #  only testplans are implicit (get multiple)
      indexed = inputs.index_docs('configs/*yak*')
      self.assertEquals({os.path.abspath(fname) for fname in  {'configs/yak_m.yaml'}},
                        {doc.path
                         for doc in indexed.of_type(inputs.MANIFEST_SCHEMA.primary_type)})
      self.assertEquals({os.path.abspath(fname) for fname in
                         {'configs/woodchuck_t.yaml',
                          'configs/vicuna_t.yaml',
                          'configs/some.yaml',
                          'alternate-configs/woodchuck_t.yaml',
                          'alternate-configs/vicuna_t.yaml',
                          'alternate-configs/some.yaml',
                          'multidocs/bee.yaml',
                          'multidocs/mosquito.yaml',
                          'multidocs/ant.yaml'}},
                        {doc.path
                         for doc in indexed.of_type(inputs.TESTPLAN_SCHEMA.primary_type)})
      self.assertEquals(set(),
                        {doc.path
                         for doc in indexed.of_type(parser.SCHEMA_TYPE_ABSENT)})

      # Explicitly specify a testplan file (only 1):
      #  only manifests are implicit (get multiple)
      indexed = inputs.index_docs('configs/woodchuck*')
      self.assertEquals({os.path.abspath(fname) for fname in
                         {'configs/zebra_m.yaml',
                          'configs/yak_m.yaml',
                          'alternate-configs/zebra_m.yaml',
                          'alternate-configs/yak_m.yaml',
                          'multidocs/bee.yaml',
                          'multidocs/mosquito.yaml',
                          'multidocs/ant.manifest.yaml'}},
                        {doc.path
                         for doc in indexed.of_type(inputs.MANIFEST_SCHEMA.primary_type)})
      self.assertEquals({os.path.abspath(fname) for fname in  {'configs/woodchuck_t.yaml'}},
                        {doc.path
                         for doc in indexed.of_type(inputs.TESTPLAN_SCHEMA.primary_type)})
      self.assertEquals(set(),
                        {doc.path
                         for doc in indexed.of_type(parser.SCHEMA_TYPE_ABSENT)})


      # Specific directory, all files are configs.
      indexed = inputs.index_docs('configs')
      self.assertEquals({os.path.abspath(fname) for fname in
                         {'configs/zebra_m.yaml',
                          'configs/yak_m.yaml'}},
                        {doc.path
                         for doc in indexed.of_type(inputs.MANIFEST_SCHEMA.primary_type)})
      self.assertEquals({os.path.abspath(fname) for fname in
                         {'configs/woodchuck_t.yaml',
                          'configs/vicuna_t.yaml',
                          'configs/some.yaml'}},
                        {doc.path
                         for doc in indexed.of_type(inputs.TESTPLAN_SCHEMA.primary_type)})
      self.assertEquals(set(),
                        {doc.path
                         for doc in indexed.of_type(parser.SCHEMA_TYPE_ABSENT)})

      # Match multiple manifest files explicitly, restrict additional files to a directory
      indexed = inputs.index_docs('**/*yak*', 'configs')
      self.assertEquals({os.path.abspath(fname) for fname in  {'configs/yak_m.yaml',
                                                               'configs/zebra_m.yaml',
                                                               'alternate-configs/yak_m.yaml'}},
                        {doc.path
                         for doc in indexed.of_type(inputs.MANIFEST_SCHEMA.primary_type)})
      self.assertEquals({os.path.abspath(fname) for fname in  {'configs/woodchuck_t.yaml',
                                                               'configs/vicuna_t.yaml',
                                                               'configs/some.yaml'}},
                        {doc.path
                         for doc in indexed.of_type(inputs.TESTPLAN_SCHEMA.primary_type)})
      self.assertEquals(set(),
                        {doc.path
                         for doc in indexed.of_type(parser.SCHEMA_TYPE_ABSENT)})

      # Match muliple testplan files explicitly, restrict additional files to a directory
      indexed = inputs.index_docs('**/*woodchuck*', 'configs')
      self.assertEquals({os.path.abspath(fname) for fname in  {'configs/zebra_m.yaml',
                                                               'configs/yak_m.yaml'}},
                        {doc.path
                         for doc in indexed.of_type(inputs.MANIFEST_SCHEMA.primary_type)})
      self.assertEquals({os.path.abspath(fname) for fname in  {'configs/woodchuck_t.yaml',
                                                               'configs/some.yaml',
                                                               'configs/vicuna_t.yaml',
                                                               'alternate-configs/woodchuck_t.yaml'}},
                        {doc.path
                         for doc in indexed.of_type(inputs.TESTPLAN_SCHEMA.primary_type)})
      self.assertEquals(set(),
                        {doc.path
                         for doc in indexed.of_type(parser.SCHEMA_TYPE_ABSENT)})



@contextmanager
def pushd(new_dir):
  """A contextmanager that scopes being in a specified dir (like pushd)"""
  previous_dir = os.getcwd()
  os.chdir(new_dir)
  try:
    yield
  finally:
    os.chdir(previous_dir)
