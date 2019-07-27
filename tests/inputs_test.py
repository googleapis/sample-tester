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
    self.assertEquals(inputs.MANIFEST_TYPE,
                      inputs.untyped_yaml_resolver(
                          parser.Document('/my/path/to/some.manifest.yaml', None)))
    self.assertEquals(inputs.TESTPLAN_TYPE,
                      inputs.untyped_yaml_resolver(
                          parser.Document('path/to/some.yaml', None)))
    self.assertEquals(inputs.UNKNOWN_TYPE,
                      inputs.untyped_yaml_resolver(
                          parser.Document('path/to/some.txt', None)))

  def test_get_globbed(self):
    with pushd(os.path.join(_ABS_DIR, 'testdata', 'inputs')):
      self.assertEquals(set(), inputs.get_globbed())
      self.assertEquals(set(), inputs.get_globbed(''))
      self.assertEquals({'configs', 'data'}, inputs.get_globbed('*'))
      self.assertEquals({'configs', 'data'}, inputs.get_globbed('**'))
      self.assertEquals({'configs/zebra_m.yaml',
                         'configs/yak_m.yaml',
                         'configs/woodchuck_t.yaml',
                         'configs/vicuna_t.yaml',
                         'configs/some.yaml',
                         'configs/other.yaml',
                         'configs/some.txt',
                         'data/datafile.txt'},
                        set(inputs.get_globbed('**/*')))
      self.assertEquals({'configs/zebra_m.yaml',
                         'configs/yak_m.yaml'},
                        set(inputs.get_globbed('**/*_m*')))

  def test_index_docs_configs(self):
    with pushd(os.path.join(_ABS_DIR, 'testdata', 'inputs')):
      indexed = inputs.index_docs('configs/*.yaml')
      self.assertEquals(set(map(os.path.abspath, {'configs/zebra_m.yaml',
                                                  'configs/yak_m.yaml'})),
                        set([doc.path
                             for doc in indexed.of_type(inputs.MANIFEST_TYPE)]))
      self.assertEquals(set(map(os.path.abspath, { 'configs/woodchuck_t.yaml',
                                                   'configs/vicuna_t.yaml',
                                                   'configs/some.yaml'})),
                        set([doc.path
                             for doc in indexed.of_type(inputs.TESTPLAN_TYPE)]))
      self.assertEquals(set(),
                        set([doc.path
                             for doc in indexed.of_type(parser.SCHEMA_TYPE_ABSENT)]))

  def test_index_docs_implicit(self):
    with pushd(os.path.join(_ABS_DIR, 'testdata', 'inputs')):
      # All files are configs.
      indexed = inputs.index_docs()
      self.assertEquals(set(map(os.path.abspath, {'configs/zebra_m.yaml',
                                                  'configs/yak_m.yaml'})),
                        set([doc.path
                             for doc in indexed.of_type(inputs.MANIFEST_TYPE)]))
      self.assertEquals(set(map(os.path.abspath, { 'configs/woodchuck_t.yaml',
                                                   'configs/vicuna_t.yaml'})),
                        set([doc.path
                             for doc in indexed.of_type(inputs.TESTPLAN_TYPE)]))
      self.assertEquals(set(map(os.path.abspath, {'configs/some.yaml'})),
                        set([doc.path
                             for doc in indexed.of_type(parser.SCHEMA_TYPE_ABSENT)]))

      # Explicitly specify a manifest file (only 1):
      #  only testplans are implicit (get 2)
      indexed = inputs.index_docs('**/*yak*')
      self.assertEquals(set(map(os.path.abspath, {'configs/yak_m.yaml'})),
                        set([doc.path
                             for doc in indexed.of_type(inputs.MANIFEST_TYPE)]))
      self.assertEquals(set(map(os.path.abspath, { 'configs/woodchuck_t.yaml',
                                                   'configs/vicuna_t.yaml'})),
                        set([doc.path
                             for doc in indexed.of_type(inputs.TESTPLAN_TYPE)]))
      self.assertEquals(set(map(os.path.abspath, {'configs/some.yaml'})),
                        set([doc.path
                             for doc in indexed.of_type(parser.SCHEMA_TYPE_ABSENT)]))

      # Explicitly specify a testplan file (only 1):
      #  only manifests are implicit (get 2)
      indexed = inputs.index_docs('**/*woodchuck*')
      self.assertEquals(set(map(os.path.abspath, {'configs/zebra_m.yaml',
                                                  'configs/yak_m.yaml'})),
                        set([doc.path
                             for doc in indexed.of_type(inputs.MANIFEST_TYPE)]))
      self.assertEquals(set(map(os.path.abspath, {'configs/woodchuck_t.yaml'})),
                        set([doc.path
                             for doc in indexed.of_type(inputs.TESTPLAN_TYPE)]))
      self.assertEquals(set(),
                        set([doc.path
                             for doc in indexed.of_type(parser.SCHEMA_TYPE_ABSENT)]))



@contextmanager
def pushd(new_dir):
  """A contextmanager that scopes being in a specified dir (like pushd)"""
  previous_dir = os.getcwd()
  os.chdir(new_dir)
  try:
    yield
  finally:
    os.chdir(previous_dir)
