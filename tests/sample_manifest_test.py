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

from sampletester import inputs
from sampletester import parser
from sampletester import sample_manifest

_ABS_FILE = os.path.abspath(__file__)
_ABS_DIR = os.path.dirname(_ABS_FILE)


class TestManifestV3(unittest.TestCase):
  def test_multiple_yaml_docs_in_stream(self):
    # all_parsed = sample_manifest.strings_to_yaml(
    indexed_docs = parser.IndexedDocs(
        resolver=lambda _: sample_manifest.SCHEMA.primary_type,
        strict=False)
    indexed_docs.from_strings(('january',
                               """---
who: alice
---
who: bob
"""),
        ('december',
         """---
who: carol
---
who: dan
"""))
    all_parsed = sample_manifest.from_indexed_docs(indexed_docs)
    found = {}
    for _, doc, _ in all_parsed:
      found[doc["who"]] = True
    self.assertEqual(4, len(found))
    self.assertTrue(all([name in found for name in ['alice', 'bob', 'carol', 'dan']]))

  def test_read_no_version(self):
    manifest_source, _ = self.get_manifest_source()
    manifest_source[1].pop(sample_manifest.SCHEMA.version_key)
    manifest = sample_manifest.Manifest('language', 'sample')
    with self.assertRaises(Exception):
      manifest.read_sources([manifest_source])

  def test_read_invalid_version(self):
    manifest_source, _ = self.get_manifest_source()
    manifest_source[1][sample_manifest.SCHEMA.version_key] = 'foo'
    manifest = sample_manifest.Manifest('language', 'sample')
    with self.assertRaises(Exception):
      manifest.read_sources([manifest_source])

  def test_read_no_type(self):
    manifest_source, _ = self.get_manifest_source()
    manifest_source[1].pop(sample_manifest.SCHEMA.type_key)
    manifest = sample_manifest.Manifest('language', 'sample')
    manifest.read_sources([manifest_source])
    with self.assertRaises(Exception):
      manifest.index()

  def test_read_nonmanifest_type(self):
    manifest_source, _ = self.get_manifest_source()
    manifest_source[1][sample_manifest.SCHEMA.type_key] = "random"
    manifest = sample_manifest.Manifest('language', 'sample')
    manifest.read_sources([manifest_source])
    manifest.index()
    # The above should yield no assertion


  def test_get_(self):
    self.do_test_get_(self.get_manifest_source)

  def test_get_with_implicits(self):
    self.do_test_get_(self.get_manifest_source_with_implicits)

  def do_test_get_(self, getter):
    manifest_source, (expect_alice, expect_bob, expect_carol, expect_dan) = getter()

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


  def test_get_keys(self):
    manifest_source, (expect_alice, expect_bob, expect_carol,
                      expect_dan) = self.get_manifest_source()

    manifest = sample_manifest.Manifest('language', 'sample')
    manifest.read_sources([manifest_source])
    manifest.index()
    self.assertEqual(['python', ''], manifest.get_keys())
    self.assertEqual(['alice', 'robert'], manifest.get_keys('python'))
    self.assertEqual([], manifest.get_keys('python', 'alice'))
    self.assertEqual([], manifest.get_keys('python', 'robert'))
    self.assertEqual(['math'], manifest.get_keys(''))
    self.assertEqual([], manifest.get_keys('', 'math'))

    self.assertEqual([], manifest.get_keys('python', 'alice','zoe'))
    self.assertEqual([], manifest.get_keys('zoe'))
    self.assertEqual([], manifest.get_keys('python', 'zoe'))


  def test_get_one(self):
    manifest_source, (expect_alice, expect_bob, expect_carol,
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

    self.assertRaises(sample_manifest.ItemNotUniqueError,
                      manifest.get_one, '', 'math')

  def test_get_all_elements(self):
    manifest_source, (expect_alice, expect_bob, expect_carol,
                      expect_dan) = self.get_manifest_source()

    manifest = sample_manifest.Manifest('language', 'sample')
    manifest.read_sources([manifest_source])
    manifest.index()

    all_elements = [x for x in manifest.get_all_elements()]
    self.assertEqual([expect_alice, expect_bob, expect_carol, expect_dan],
                     all_elements)


  def get_manifest_source(self):
    list_name = 'mysamples'
    manifest = {
        sample_manifest.SCHEMA.type_key:
            '{}/{}'.format(sample_manifest.SCHEMA.primary_type,
                           list_name),
        sample_manifest.SCHEMA.version_key: 3,
        list_name: [
            {
                'language': 'python',
                'path': '/home/nobody/api/samples/trivial/method/sample_alice',
                'sample': 'alice',
                'canonical': 'trivial'
            },
            {
                'language': 'python',
                'path': '/home/nobody/api/samples/complex/method/usecase_bob',
                'sample': 'robert',
                'tag': 'guide'
            },
            {
                'path': '/tmp/newer/carol',
                'sample': 'math'
            }, {
                'path': '/tmp/newest/dan',
                'sample': 'math'
            }
        ]
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
    return (('valid_manifest', manifest, {}),
            (expect_alice, expect_bob, expect_carol, expect_dan))

  def get_manifest_source_with_implicits(self):
    list_name = 'mysamples'
    manifest = {
        sample_manifest.SCHEMA.type_key:
            '{}/{}'.format(sample_manifest.SCHEMA.primary_type,
                           list_name),
        sample_manifest.SCHEMA.version_key: 3,
        list_name: [
            {
                'language': 'python',
                'path': '/home/nobody/api/samples/trivial/method/sample_alice',
                'sample': 'alice',
                'canonical': 'trivial'
            },
            {
                'language': 'python',
                'path': '/home/nobody/api/samples/complex/method/usecase_bob',
                'sample': 'robert',
                'tag': 'guide'
            },
            {
                'path': '/tmp/newer/carol',
                'sample': 'math'
            }, {
                'path': '/tmp/newest/dan',
                'sample': 'math'
            }
        ]
    }

    expect_alice = {
        'path': '/home/nobody/api/samples/trivial/method/sample_alice',
        'language': 'python',
        'sample': 'alice',
        'canonical': 'trivial',
        '@datum': 'value',
        'info': 'data'
    }
    expect_bob = {
        'path': '/home/nobody/api/samples/complex/method/usecase_bob',
        'language': 'python',
        'sample': 'robert',
        'tag': 'guide',
        '@datum': 'value',
        'info': 'data'
    }
    expect_carol = {
        'path': '/tmp/newer/carol',
        'sample': 'math',
        '@datum': 'value',
        'info': 'data'
    }
    expect_dan = {
        'path': '/tmp/newest/dan',
        'sample': 'math',
        '@datum': 'value',
        'info': 'data'
    }
    implicit_tags = {'@datum': 'value', 'info': 'data'}
    return (('valid_manifest', manifest, implicit_tags),
            (expect_alice, expect_bob, expect_carol, expect_dan))

  def get_manifest_source_braces_correct(self, version):
    list_name = 'mysamples'
    manifest = {
        sample_manifest.SCHEMA.type_key:
            '{}/{}'.format(sample_manifest.SCHEMA.primary_type,
                           list_name),
        sample_manifest.SCHEMA.version_key: 3,
        list_name: [
            {
                'greetings': 'teatime-{name}{{',
                'fond_wish': 'hope{{',
                'form': 'Would you like some {drink}? {{maybe}}',
                'base_drink': 'tea',
                'name': 'Mary',
                'drink': '{base_drink} with milk',
                'interruption': 'Excuse me, {name}. {form}'
            }
        ]
    }
    return ('manifest with braces', manifest, {})

  def test_braces(self):   ### combine with above
    list_name = 'mysamples'
    manifest_content = {
        sample_manifest.SCHEMA.type_key:
            '{}/{}'.format(sample_manifest.SCHEMA.primary_type,
                           list_name),
        sample_manifest.SCHEMA.version_key: 3,
        list_name: [
            {
                'greetings': 'teatime-{name}{{',
                'fond_wish': 'hope{{',
                'form': 'Would you like some {drink}? {{maybe}}',
                'base_drink': 'tea',
                'name': 'Mary',
                'drink': '{base_drink} with milk',
                'interruption': 'Excuse me, {name}. {form}'
            }
        ]
    }
    manifest = sample_manifest.Manifest('greetings')
    manifest.read_sources([('manifest_with_braces', manifest_content, {})])
    manifest.index()

    expect_mary = {
        'name': 'Mary',
        'fond_wish': 'hope{',
        'greetings': 'teatime-Mary{',
        'form': 'Would you like some tea with milk? {maybe}',
        'base_drink': 'tea',
        'drink': 'tea with milk',
        'interruption': 'Excuse me, Mary. Would you like some tea with milk? {maybe}'
    }
    self.assertEqual(expect_mary, manifest.get_one('teatime-Mary{', name='Mary'))


  def test_braces_error_unfinished(self):
    list_name = 'mysamples'
    manifest_content = {
         sample_manifest.SCHEMA.type_key:
            '{}/{}'.format(sample_manifest.SCHEMA.primary_type,
                           list_name),
        sample_manifest.SCHEMA.version_key: 3,
        list_name: [
            {
                'greetings': 'teatime',
                'form': 'Would you like some {drink?', # error
                'base_drink': 'tea',
                'name': 'Mary',
                'drink': '{base_drink} with milk',
                'interruption': 'Excuse me, {name}. {form}'
            }
        ]
    }
    manifest = sample_manifest.Manifest('greetings')
    manifest.read_sources([('erroring manifest', manifest_content, {})])
    self.assertRaises(sample_manifest.ManifestSyntaxError, manifest.index)

  def test_braces_error_unfinished_at_end(self):
    list_name = 'mysamples'
    manifest_content = {
         sample_manifest.SCHEMA.type_key:
            '{}/{}'.format(sample_manifest.SCHEMA.primary_type,
                           list_name),
        sample_manifest.SCHEMA.version_key: 3,
        list_name: [
            {
                'greetings': 'teatime',
                'form': 'Would you like some {', # error
                'base_drink': 'tea',
                'name': 'Mary',
                'drink': '{base_drink} with milk',
                'interruption': 'Excuse me, {name}. {form}'
            }
        ]
    }
    manifest = sample_manifest.Manifest('greetings')
    manifest.read_sources([('erroring manifest', manifest_content, {})])
    self.assertRaises(sample_manifest.ManifestSyntaxError, manifest.index)

  def test_braces_error_empty(self):
    list_name = 'mysamples'
    manifest_content = {
         sample_manifest.SCHEMA.type_key:
            '{}/{}'.format(sample_manifest.SCHEMA.primary_type,
                           list_name),
        sample_manifest.SCHEMA.version_key: 3,
        list_name: [
            {
                'greetings': 'teatime',
                'form': 'Would you like some {}?', # error
                'base_drink': 'tea',
                'name': 'Mary',
                'drink': '{base_drink} with milk',
                'interruption': 'Excuse me, {name}. {form}'
                }
        ]
    }
    manifest = sample_manifest.Manifest('greetings')
    manifest.read_sources([('erroring manifest', manifest_content, {})])
    self.assertRaises(sample_manifest.ManifestSyntaxError, manifest.index)

  def test_braces_error_key_with_braces(self):
    list_name = 'mysamples'
    manifest_content = {
         sample_manifest.SCHEMA.type_key:
            '{}/{}'.format(sample_manifest.SCHEMA.primary_type,
                           list_name),
        sample_manifest.SCHEMA.version_key: 3,
        list_name: [
            {
                'greetings': 'teatime',
                'form': 'Would you like some {drink{yea}}}?', # error
                'base_drink{yea}}': 'tea',
                'name': 'Mary',
                'drink': '{base_drink} with milk',
                'interruption': 'Excuse me, {name}. {form}'
                }
        ]
    }
    manifest = sample_manifest.Manifest('greetings')
    manifest.read_sources([('erroring manifest', manifest_content, {})])
    self.assertRaises(sample_manifest.ManifestSyntaxError, manifest.index)

  def test_braces_error_loop(self):
    list_name = 'mysamples'
    manifest_content = {
         sample_manifest.SCHEMA.type_key:
            '{}/{}'.format(sample_manifest.SCHEMA.primary_type,
                           list_name),
        sample_manifest.SCHEMA.version_key: 3,
        list_name: [
            {
                'greetings': '{drink} time',
                'form': 'It is {greetings}. Would you like some {drink}?',
                'base_drink': 'tea',
                'name': 'Mary',
                'drink': '{base_drink} with milk',
                'greetings': ' {form}', # cycle
                'interruption': 'Excuse me, {name}. {form}'
            }
        ]
    }
    manifest = sample_manifest.Manifest('greetings')
    manifest.read_sources([('erroring manifest', manifest_content, {})])
    self.assertRaises(sample_manifest.CycleError, manifest.index)

  def test_extend_all_with(self):
    manifest = [
      {
          "H": "hydrogen",
          "He": "helium",
      },
      {
          "Li": "lithium",
          "Be": "Beryllium",
      }
    ]

    add = {
      "Pb": "lead"
    }

    expected = [
        {
            "H": "hydrogen",
            "He": "helium",
            "Pb": "lead"
        },
        {
            "Li": "lithium",
            "Be": "Beryllium",
            "Pb": "lead"
        }
    ]
    self.assertEqual(expected, sample_manifest.extend_all_with(add, manifest))
    self.assertEqual(manifest, sample_manifest.extend_all_with(None, manifest))
    self.assertEqual(None, sample_manifest.extend_all_with(add, None))

  def test_check_tag_names(self):
    invalid_manifest = [
      {
          "H": "hydrogen",
          "@He": "helium",
      },
      {
          "Li": "lithium",
          "Be": "Beryllium",
      }
    ]
    with self.assertRaises(sample_manifest.ManifestSyntaxError):
      sample_manifest.check_tag_names(invalid_manifest)

    correct_manifest = [
      {
          "H": "hydrogen",
          "He": "he@lium",
      },
      {
          "Li": "@lithium",
          "Be@": "Beryllium",
      }
    ]
    self.assertEqual(correct_manifest,
                      sample_manifest.check_tag_names(correct_manifest))

  def test_read_files_with_implicit_tags(self):
    manifest_dir = os.path.abspath(os.path.join(_ABS_DIR,
                                                'testdata',
                                                'sample_manifest'))
    manifest_h_he_path = os.path.join(manifest_dir,
                                      'h_he',
                                      '12.manifest.yaml')
    manifest_li_be_path = os.path.join(manifest_dir,
                                       'li_be',
                                       '34.manifest.yaml')
    manifest_h_he_dir = os.path.dirname(manifest_h_he_path)
    manifest_li_be_dir = os.path.dirname(manifest_li_be_path)


    manifest = sample_manifest.Manifest('model', 'sample')
    manifest.from_docs(inputs.create_indexed_docs(manifest_h_he_path,
                                                  manifest_li_be_path))
    manifest.index()

    expect_hydrogen = {
        'model': 'periodic',
        'sample': 'hydrogen',
        sample_manifest.IMPLICIT_TAG_SOURCE: manifest_h_he_path,
        sample_manifest.IMPLICIT_TAG_DIR: manifest_h_he_dir,
    }
    expect_helium = {
        'model': 'periodic',
        'sample': 'helium',
        sample_manifest.IMPLICIT_TAG_SOURCE: manifest_h_he_path,
        sample_manifest.IMPLICIT_TAG_DIR: manifest_h_he_dir,
    }
    expect_lithium = {
        'model': 'periodic',
        'sample': 'lithium',
        sample_manifest.IMPLICIT_TAG_SOURCE: manifest_li_be_path,
        sample_manifest.IMPLICIT_TAG_DIR: manifest_li_be_dir,
    }
    expect_beryllium = {
        'model': 'periodic',
        'sample': 'beryllium',
        sample_manifest.IMPLICIT_TAG_SOURCE: manifest_li_be_path,
        sample_manifest.IMPLICIT_TAG_DIR: manifest_li_be_dir,
    }
    self.assertEqual([expect_hydrogen], manifest.get('periodic', 'hydrogen'))
    self.assertEqual([expect_helium], manifest.get('periodic', 'helium'))
    self.assertEqual([expect_lithium], manifest.get('periodic', 'lithium'))
    self.assertEqual([expect_beryllium], manifest.get('periodic', 'beryllium'))

if __name__ == '__main__':
  unittest.main()
