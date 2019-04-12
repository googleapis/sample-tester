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

from sampletester import sample_manifest


class TestManifest(unittest.TestCase):

  def test_read_no_version(self):
    manifest_source = self.get_manifest_source()
    manifest_source[0][1].pop('version')
    manifest = sample_manifest.Manifest('language', 'sample')
    with self.assertRaises(Exception):
      manifest.read_sources([manifest_source])

  def test_read_invalid_version(self):
    manifest_source = self.get_manifest_source()
    manifest_source[0][1]['version'] = 'foo'
    manifest = sample_manifest.Manifest('language', 'sample')
    with self.assertRaises(Exception):
      manifest.read_sources(manifest_source)

  def test_get_(self):
    manifest_source, expect_alice, expect_bob, expect_carol, expect_dan = self.get_manifest_source(
    )

    manifest = sample_manifest.Manifest('language', 'sample')
    manifest.read_sources([manifest_source])
    manifest.index()

    self.assertEqual([expect_alice], manifest.get('python', 'alice'))
    self.assertEqual([expect_alice],
                     manifest.get('python', 'alice', canonical='trivial'))
    self.assertEqual([expect_alice],
                     manifest.get('python', 'alice', path=expect_alice['path']))
    self.assertEqual([], manifest.get('python', 'alice', foo='bar'))

    self.assertEqual([expect_bob], manifest.get('python', 'robert'))
    self.assertEqual([expect_bob], manifest.get(
        'python', 'robert', tag='guide'))
    self.assertEqual([expect_bob],
                     manifest.get('python', 'robert', path=expect_bob['path']))

    self.assertEqual([expect_carol],
                     manifest.get('', 'math', path=expect_carol['path']))
    self.assertEqual([expect_dan],
                     manifest.get('', 'math', path=expect_dan['path']))

    self.assertIsNone(manifest.get('foo', 'alice'))

    math = list(manifest.get('', 'math'))
    for x in [expect_carol, expect_dan]:
      math.remove(x)
    self.assertEqual(0, len(math))

  def test_get_one(self):
    (manifest_source, expect_alice, expect_bob, expect_carol,
     expect_dan) = self.get_manifest_source()

    manifest = sample_manifest.Manifest('language', 'sample')
    manifest.read_sources([manifest_source])
    manifest.index()

    self.assertEqual(expect_alice, manifest.get_one('python', 'alice'))
    self.assertEqual(expect_alice,
                     manifest.get_one('python', 'alice', canonical='trivial'))
    self.assertEqual(
        expect_alice,
        manifest.get_one('python', 'alice', path=expect_alice['path']))
    self.assertIsNone(manifest.get_one('python', 'alice', foo='bar'))

    self.assertEqual(expect_bob, manifest.get_one('python', 'robert'))
    self.assertEqual(expect_bob,
                     manifest.get_one('python', 'robert', tag='guide'))
    self.assertEqual(
        expect_bob, manifest.get_one(
            'python', 'robert', path=expect_bob['path']))

    self.assertEqual(expect_carol,
                     manifest.get_one('', 'math', path=expect_carol['path']))
    self.assertEqual(expect_dan,
                     manifest.get_one('', 'math', path=expect_dan['path']))

    self.assertIsNone(manifest.get_one('foo', 'alice'))

    self.assertIsNone(manifest.get_one('', 'math'))

  def get_manifest_source(self):
    manifest = {
        sample_manifest.Manifest.VERSION_KEY:
            1,
        sample_manifest.Manifest.SETS_KEY:
            [{
                'language':
                    'python',
                'path':
                    '/home/nobody/api/samples/',
                sample_manifest.Manifest.ELEMENTS_KEY:
                    [{
                        'path': 'trivial/method/sample_alice',
                        'sample': 'alice',
                        'canonical': 'trivial'
                    },
                     {
                         'path': 'complex/method/usecase_bob',
                         'sample': 'robert',
                         'tag': 'guide'
                     }]
            },
             {
                 'path':
                     '/tmp/',
                 sample_manifest.Manifest.ELEMENTS_KEY: [{
                     'path': 'newer/carol',
                     'sample': 'math'
                 }, {
                     'path': 'newest/dan',
                     'sample': 'math'
                 }]
             }]
    }

    expect_alice = {
        'path': '/home/nobody/api/samples/trivial/method/sample_alice',
        'language': 'python',
        'sample': 'alice',
        'canonical': 'trivial'
    }
    expect_bob = {
        'path': '/home/nobody/api/samples/complex/method/usecase_bob',
        'language': 'python',
        'sample': 'robert',
        'tag': 'guide'
    }
    expect_carol = {'path': '/tmp/newer/carol', 'sample': 'math'}
    expect_dan = {'path': '/tmp/newest/dan', 'sample': 'math'}
    return ('valid_manifest',
            manifest), expect_alice, expect_bob, expect_carol, expect_dan


  def get_manifest_source_braces_correct(self, version):
    manifest = {
        sample_manifest.Manifest.VERSION_KEY:
            version,
        sample_manifest.Manifest.SETS_KEY:
            [{
                'greetings': 'teatime',
                'form': 'Would you like some {drink}?',
                'drink': 'tea',
                sample_manifest.Manifest.ELEMENTS_KEY:
                    [{
                        'name': 'Mary',
                        'drink': ' with milk',
                        'interruption': 'Excuse me, {name}. {form}'
                    }]
                }]
        }
    return ('manifest with braces', manifest)

  def test_braces_v1(self):
    manifest_source = self.get_manifest_source_braces_correct(1)
    manifest = sample_manifest.Manifest('greetings')
    manifest.read_sources([manifest_source])
    manifest.index()

    expect_mary = {
        'name': 'Mary',
        'greetings': 'teatime',
        'form': 'Would you like some {drink}?',
        'drink': 'tea with milk',
        'interruption': 'Excuse me, {name}. {form}'
    }

    self.assertEqual(expect_mary, manifest.get_one('teatime', name='Mary'))


if __name__ == '__main__':
  unittest.main()
