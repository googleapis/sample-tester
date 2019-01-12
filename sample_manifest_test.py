import unittest
import sample_manifest

class TestManifest(unittest.TestCase):
  def test_read_valid(self):
    """This is a white-box test of the implementation.

    There are black-box tests that test the input and output for these cases.
    """

    valid_manifest_file, expect_alice, expect_bob, expect_carol, expect_dan = self.get_valid_manifest()

    manifest = sample_manifest.Manifest()
    self.assertEqual(1, len(manifest.read_strings(valid_manifest_file)))

    self.assertEqual(2, len(manifest.tags))
    self.assertEqual(4, len(manifest.tags['python']))
    self.assertEqual(2, len(manifest.tags['python']['region_tag']))
    self.assertEqual(1, len(manifest.tags['python']['canonical']))
    self.assertEqual(1, len(manifest.tags['python']['tag']))
    self.assertEqual(2, len(manifest.tags['python']['path']))
    self.assertEqual([expect_alice], manifest.tags['python']['region_tag']['alice'])
    self.assertEqual([expect_alice], manifest.tags['python']['canonical']['trivial'])
    self.assertEqual([expect_alice], manifest.tags['python']['path'][expect_alice['path']])
    self.assertEqual([expect_bob], manifest.tags['python']['region_tag']['robert'])
    self.assertEqual([expect_bob], manifest.tags['python']['tag']['guide'])
    self.assertEqual([expect_bob], manifest.tags['python']['path'][expect_bob['path']])

    self.assertEqual(2, len(manifest.tags['']))
    self.assertEqual(1, len(manifest.tags['']['region_tag']))
    self.assertEqual(2, len(manifest.tags['']['path']))
    self.assertEqual([expect_carol], manifest.tags['']['path'][expect_carol['path']])
    self.assertEqual([expect_dan], manifest.tags['']['path'][expect_dan['path']])
    math = list(manifest.tags['']['region_tag']['math'])
    for x in [expect_carol, expect_dan]:
      math.remove(x)
    self.assertEqual(0, len(math))


  def test_read_no_version(self):
    manifest_file = (
        'sample_sets:   \n'+
        '- language: python   \n'+
        '  base_dir : /home/nobody/api/samples   \n'+
        '  samples :   \n'+
        '    trivial/method/sample_alice:   \n'+
        '      region_tag: alice   \n'+
        '      canonical: trivial   \n')

    manifest = sample_manifest.Manifest()
    with self.assertRaises(Exception):
      manifest.read_strings(manifest_file)


  def test_read_invalid_version(self):
    manifest_file = (
        'version: foo   \n'+
        'sample_sets:   \n'+
        '- language: python   \n'+
        '  base_dir : /home/nobody/api/samples   \n'+
        '  samples :   \n'+
        '    trivial/method/sample_alice:   \n'+
        '      region_tag: alice   \n'+
        '      canonical: trivial   \n')

    manifest = sample_manifest.Manifest()
    with self.assertRaises(Exception):
      manifest.read_strings(manifest_file)

  def test_get_(self):
    valid_manifest_file, expect_alice, expect_bob, expect_carol, expect_dan = self.get_valid_manifest()

    manifest = sample_manifest.Manifest()
    manifest.read_strings(valid_manifest_file)

    self.assertEqual([expect_alice], manifest.get('python','region_tag','alice'))
    self.assertEqual([expect_alice], manifest.get('python','canonical','trivial'))
    self.assertEqual([expect_alice], manifest.get('python','path', expect_alice['path']))

    self.assertEqual([expect_bob], manifest.get('python','region_tag','robert'))
    self.assertEqual([expect_bob], manifest.get('python','tag', 'guide'))
    self.assertEqual([expect_bob], manifest.get('python','path', expect_bob['path']))

    self.assertEqual([expect_carol], manifest.get('','path', expect_carol['path']))
    self.assertEqual([expect_dan], manifest.get('','path', expect_dan['path']))

    self.assertIsNone(manifest.get('foo','region_tag','alice'))

    math = list(manifest.get('','region_tag','math'))
    for x in [expect_carol, expect_dan]:
      math.remove(x)
    self.assertEqual(0, len(math))

  def test_get_one(self):
    valid_manifest_file, expect_alice, expect_bob, expect_carol, expect_dan = self.get_valid_manifest()

    manifest = sample_manifest.Manifest()
    manifest.read_strings(valid_manifest_file)

    self.assertEqual(expect_alice, manifest.get_one('python','region_tag','alice'))
    self.assertEqual(expect_alice, manifest.get_one('python','canonical','trivial'))
    self.assertEqual(expect_alice, manifest.get_one('python','path', expect_alice['path']))

    self.assertEqual(expect_bob, manifest.get_one('python','region_tag','robert'))
    self.assertEqual(expect_bob, manifest.get_one('python','tag', 'guide'))
    self.assertEqual(expect_bob, manifest.get_one('python','path', expect_bob['path']))

    self.assertEqual(expect_carol, manifest.get_one('','path', expect_carol['path']))
    self.assertEqual(expect_dan, manifest.get_one('','path', expect_dan['path']))

    self.assertIsNone(manifest.get_one('foo','region_tag','alice'))

    self.assertIsNone(manifest.get_one('','region_tag','math'))


  def get_valid_manifest(self):
    valid_manifest_file = (
        'version: 1   \n'+
        'sample_sets:   \n'+
        '- language: python   \n'+
        '  base_dir : /home/nobody/api/samples   \n'+
        '  samples :   \n'+
        '    trivial/method/sample_alice:   \n'+
        '      region_tag: alice   \n'+
        '      canonical: trivial   \n'+
        '    complex/method/usecase_bob:   \n'+
        '      region_tag: robert   \n'+
        '      tag: guide   \n'+
        '- base_dir: /tmp   \n'+
        '  samples:   \n'+
        '    newer/carol:   \n'+
        '      region_tag: math   \n'+
        '    newest/dan:   \n'+
        '      region_tag: math   \n')

    expect_alice = { 'path': '/home/nobody/api/samples/trivial/method/sample_alice', 'region_tag': 'alice', 'canonical': 'trivial'}
    expect_bob = { 'path': '/home/nobody/api/samples/complex/method/usecase_bob', 'region_tag': 'robert', 'tag': 'guide'}
    expect_carol = { 'path': '/tmp/newer/carol', 'region_tag': 'math'}
    expect_dan = { 'path': '/tmp/newest/dan', 'region_tag': 'math'}
    return valid_manifest_file, expect_alice, expect_bob, expect_carol, expect_dan


if __name__ == '__main__':
    unittest.main()
