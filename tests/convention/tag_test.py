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

import os
import unittest

from sampletester.convention import tag
from sampletester import sample_manifest

_ABS_FILE = os.path.abspath(__file__)
_ABS_DIR = os.path.dirname(_ABS_FILE)

class TestSubstitution(unittest.TestCase):
  def test_substitution(self):
    self.assertEqual('hi there',        tag.insert_into('hi there',         ('@here', 'foo')))
    self.assertEqual('hi @there',       tag.insert_into('hi @there',        ('@here', 'foo')))
    self.assertEqual('hi @there',       tag.insert_into('hi @@there',       ('@here', 'foo')))
    self.assertEqual('hi foo there',    tag.insert_into('hi @here there',   ('@here', 'foo')))
    self.assertEqual('hi @here there', tag.insert_into('hi @@here there',   ('@here', 'foo')))
    self.assertEqual('hi @foo there',  tag.insert_into('hi @@@here there',  ('@here', 'foo')))

    self.assertEqual('hi @foo there foo @greetings @@all',
                     tag.insert_into('hi @@@here there @here @@greetings @@@all', ('@here', 'foo')))
    self.assertRaises(tag.InternalInvalidPlaceholderDefinition,
                      tag.insert_into, 'hi @here', ('$here', 'foo'))

class TestArgSubstitution(unittest.TestCase):
  def setUp(self):
    filename = full_path('testdata/tag_test.manifest.yaml')
    manifest = sample_manifest.Manifest('situation')
    manifest.read_files(filename)
    manifest.index()
    self.env = tag.ManifestEnvironment(filename, '', manifest, [])

  def get_call_only(self, *args, **kwargs):
    call, _ = self.env.get_call(*args, **kwargs)
    return call

  def test_simple_invocation(self):
    self.assertEqual('Zimbabwe is a country',
                     self.get_call_only('simple', '--continent=Africa'))

    self.assertEqual('Zimbabwe is a country',
                     self.get_call_only('simple', continent='Africa'))

  def test_invocation_with_placeholder(self):
    self.assertEqual(r'Ecuador "--continent=\"South America\"" is @a @country',
                     self.get_call_only('invocation-with-placeholder',
                                        '--continent="South America"'))
    self.assertEqual(r'Ecuador --continent="South America" is @a @country',
                     self.get_call_only('invocation-with-placeholder',
                                        continent='South America'))

    self.assertEqual(r'Ecuador "--continent=\"South @@America\"" is @a @country',
                     self.get_call_only('invocation-with-placeholder',
                                        '--continent="South @@@America"'))
    self.assertEqual(r'Ecuador --continent="South @@America" is @a @country',
                     self.get_call_only('invocation-with-placeholder',
                                        continent='South @@@America'))

  def test_invocation_with_placeholder(self):
    self.assertEqual(r'Japan @args is @a @country',
                     self.get_call_only('invocation-with-escaped-placeholder',
                                        '--continent="Asia"'))
    self.assertEqual(r'Japan @args is @a @country',
                     self.get_call_only('invocation-with-escaped-placeholder',
                                        continent='Asia'))

  def test_invocation_via_bin_no_path(self):
    self.assertEqual('France is a country "--continent=Europe"',
                     self.get_call_only('invocation-via-bin-no-path',
                                        '--continent=Europe'))
    self.assertEqual('France is a country --continent="Europe"',
                     self.get_call_only('invocation-via-bin-no-path',
                                        continent='Europe'))

  def test_invocation_via_bin_with_path(self):
    self.assertEqual(
        'Australia is a country in the south Atlantic "--continent=Australia"',
        self.get_call_only('invocation-via-bin-with-path',
                           '--continent=Australia'))
    self.assertEqual(
        'Australia is a country in the south Atlantic --continent="Australia"',
        self.get_call_only('invocation-via-bin-with-path',
                           continent='Australia'))

  def test_invocation_via_just_path(self):
    self.assertEqual('Mexico is a country "--continent=NorthAmerica"',
                     self.get_call_only('invocation-via-just-path',
                                        '--continent=NorthAmerica'))
    self.assertEqual('Mexico is a country --continent="NorthAmerica"',
                     self.get_call_only('invocation-via-just-path',
                                        continent='NorthAmerica'))

  def test_no_invocation_bin_path(self):
    self.assertRaises(Exception,
                      self.get_call_only, 'no-invocation-bin-path',
                      '--person=Alice')

  def test_no_matching_object(self):
    self.assertRaises(Exception,
                      self.get_call_only, 'no-object-with-this-value',
                      person='Bob')

class TestChangingInvocationKey(unittest.TestCase):
  def setUp(self):
    filename = full_path('testdata/tag_test.manifest.yaml')
    manifest = sample_manifest.Manifest('situation')
    manifest.read_files(filename)
    manifest.index()
    self.env = tag.ManifestEnvironment(
        filename, '', manifest, [],
        manifest_options = {'invocation': 'callthisway'})

  def get_call_only(self, *args, **kwargs):
    call, _ = self.env.get_call(*args, **kwargs)
    return call


  def test_alternate_invocation(self):
    self.assertEqual('correct way to call',
                     self.get_call_only('alternate-invocation'))


class TestChdir(unittest.TestCase):
  def setUp(self):
    filename = full_path('testdata/tag_test.manifest.yaml')
    manifest = sample_manifest.Manifest('situation')
    manifest.read_files(filename)
    manifest.index()
    self.env = tag.ManifestEnvironment(filename, '', manifest, [])

  def get_dir_only(self, *args, **kwargs):
    _, chdir = self.env.get_call(*args, **kwargs)
    return chdir

  def test_chdir(self):
    self.assertEqual(None, self.get_dir_only('no-chdir'))
    self.assertEqual('/my/foo/dir', self.get_dir_only('with-chdir'))


class TestChangingChdirKey(unittest.TestCase):
  def setUp(self):
    filename = full_path('testdata/tag_test.manifest.yaml')
    manifest = sample_manifest.Manifest('situation')
    manifest.read_files(filename)
    manifest.index()
    self.env = tag.ManifestEnvironment(
        filename, '', manifest, [],
        manifest_options = {'chdir': 'switch-dir-to'})

  def get_dir_only(self, *args, **kwargs):
    _, chdir = self.env.get_call(*args, **kwargs)
    return chdir

  def test_chdir(self):
    self.assertEqual('/the/correct/dir', self.get_dir_only('with-alternate-chdir'))


class TestGetSymbol(unittest.TestCase):
  def setUp(self):
    self.manifest_file_name = full_path('testdata/tag_test.manifest.yaml')
    manifest = sample_manifest.Manifest('situation')
    manifest.read_files(self.manifest_file_name)
    manifest.index()
    self.env = tag.ManifestEnvironment(self.manifest_file_name, '', manifest, [])

  def test_get_symbol(self):
    self.assertEqual('Ecuador @args is @@a @country',
                     self.env.get_symbol('invocation-with-placeholder:invocation'))

    expected_full = {'situation': 'invocation-with-placeholder',
                     'invocation': 'Ecuador @args is @@a @country',
                     'environment': 'Valid call',
                     '@manifest_source': self.manifest_file_name,
                     '@manifest_dir': os.path.dirname(self.manifest_file_name)
                     }
    self.assertEqual(str(expected_full),
                     self.env.get_symbol('invocation-with-placeholder'))
    self.assertEqual(str(expected_full),
                     self.env.get_symbol('invocation-with-placeholder:'))


def full_path(leaf_path):
  return os.path.join(_ABS_DIR, leaf_path)

if __name__ == '__main__':
  unittest.main()
