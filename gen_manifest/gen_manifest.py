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
import argparse
import io
import os
import re
import sys
import yaml

from collections import OrderedDict
from glob import glob
from yaml import Dumper
from yaml.representer import SafeRepresenter

ALL_LANGS = ["python", "java", "csharp", "nodejs", "ruby", "php", "go"]

def parse_args():
  parser = argparse.ArgumentParser(
      formatter_class=argparse.ArgumentDefaultsHelpFormatter,
      description=
      """A tool to generate manifest files (for use in sample-tester) purely from
      existing sample artifacts on disk. Each entry within the manifest file
      corresponds to a specific sample file on disk and lists the path to that
      file and the region tag occurring within that file. Any number of
      arbitrary key/value pairs can be specified (see the usage line) and will
      be applied to all samples listed in the manifest.""",
      usage=('%(prog)s [-h] [--schema_version SCHEMA_VERSION] ' +
             '[--output OUTPUT] [--flat] [--KEY=VALUE ...] files [files ...]'))
  parser.add_argument('--schema_version', default='2',
                      help='schema version to use in the generated manifest')
  parser.add_argument('--output',
                      help="""the name of the output file, which should include
                      the manifest.yaml` extension; if not provided, will
                      output to stdout.""")
  parser.add_argument('--flat', action='store_true',
                      help="""whether to list all labels for each item, even if
                      this leads to duplicate YAML structures""")
  parser.add_argument('files', nargs='+',
                      help="""path glob to one or more sample files, relative to the
                      current working directory""")
  (args, labels) = parser.parse_known_args()
  labels = [(parts[0][2:], parts[1]) for parts in [label.split('=', 1) for label in labels]]
  return args, labels

### For manifest schema version 3

def emit_manifest_v3(labels, sample_globs, flat):
  if flat:
    return dump(create_flat_manifest_v3(labels, sample_globs))
  return create_factored_manifest_v3(labels, sample_globs)

def create_factored_manifest_v3(labels, sample_globs):
  """Creates a factored v3 manifest with the given top-level labels

  The `basepath` at the top level is the current working directory, and the
  `path` for each individual item is a reference to `basepath` followed by the
  glob resolution for that sample. The `sample` (ID) for each item is the value
  of the single region tag inside that sample file.
  """
  lines = ['type: manifest/samples',
           'schema_version: 3',
           'base: &common']
  for name, value in labels:
    lines.append('  {}: {}'.format(name, value))
  lines.extend([
      '  basepath: {}'.format(os.getcwd()),
      'samples:'
  ])
  for s in sample_globs:
    for sample_relative_path in glob(s, recursive=True):
      sample_absolute_path = os.path.join(os.getcwd(), sample_relative_path)
      lines.extend([
          '- <<: *common',
	  '  path: {{basepath}}/{}'.format(sample_relative_path),
	  '  sample: {}'.format(get_region_tag(sample_absolute_path))
          ])
  return '\n'.join(lines) + '\n'

def create_flat_manifest_v3(labels, sample_globs):
  """Creates a flat v3 manifest with the given labels

  The `path` for each individual item is the absolute path to the current
  working directory joined with the glob resolution for that sample. The
  `sample` (ID) for each item is the value of the single region tag inside that
  sample file.
  """
  items = []
  for s in sample_globs:
    for sample in glob(s, recursive=True):
      sample_path = os.path.join(os.getcwd(), sample)
      entry = {
	  'path': sample_path,
	  'sample': get_region_tag(sample_path)
      }
      for name, value in labels:
        entry[name] = value
      items.append(entry)

  manifest = OrderedDict()
  manifest["type"] = "manifest/samples"
  manifest["schema_version"] = 3
  manifest["samples"] = items
  return manifest


### For manifest schema version 2

def emit_manifest_v2(labels, sample_globs, flat):
  return dump(create_manifest_v2(labels, sample_globs))

def create_manifest_v2(labels, sample_globs):
  """Creates a v2 manifest with the given top-level labels

  The `path` at the top level is the current working directory, and the `path`
  for each individual item is the glob resolution for that sample. The `sample` (ID)
  for each item is the value of the single region tag inside that sample file.
  """
  manifest = OrderedDict()
  manifest['version'] = 2
  manifest['sets'] = []

  environment = OrderedDict()
  for name, value in labels:
    # adjust for backward compatibility
    if name == 'env':
      if value not in ALL_LANGS:
        sys.exit('Unrecognized language "{}": env should be one of {}'
                 .format(value, ALL_LANGS))
      name = 'environment'
    environment[name] = value
  environment['path'] = os.getcwd() + "/"
  environment['__items__'] = path_sample_pairs_v2(sample_globs)
  manifest['sets'].append(environment)
  return manifest


def path_sample_pairs_v2(sample_globs):
  """Returns a list of path/ID pairs for each glob in `sample_globs`"""
  items = []
  for s in sample_globs:
    for sample in glob(s, recursive=True):
      items.append({
	  'path': sample,
	  'sample': get_region_tag(os.path.join(os.getcwd(), sample))
      })
  return items


def get_region_tag(sample_file_path):
  """Extracts the region tag from the given sample.

  Errors if the number of region tags found is not equal to one. Ignores the
  *_core tags.
  """
  start_region_tag_exp = r'\[START ([a-zA-Z0-9_]*)\]'
  end_region_tag_exp = r'\[END ([a-zA-Z0-9_]*)\]'
  region_tags = []
  with open(sample_file_path) as sample:
    sample_text = sample.read()
    start_region_tags = re.findall(start_region_tag_exp, sample_text)
    end_region_tags = re.findall(end_region_tag_exp, sample_text)

    for srt in start_region_tags:

      # We don't need those with '_cores'
      if 'core' in srt:
        continue

      if srt in end_region_tags:
        region_tags.append(srt)

  if not region_tags:
    sys.exit("Found no region tags.")

  if len(region_tags) > 1:
    sys.exit("Found too many region tags.")

  return region_tags[0]

### YAML helpers

def dict_representer(dumper, data):
  return dumper.represent_dict(data.items())

def dump(manifest):
  Dumper.add_representer(OrderedDict, dict_representer)
  Dumper.add_representer(str,
                         SafeRepresenter.represent_str)
  return yaml.dump(manifest, Dumper=Dumper, default_flow_style=False)


def main():
  args, labels = parse_args()
  if args.schema_version == '2':
    serialized_manifest = emit_manifest_v2(labels, args.files, args.flat)
  elif args.schema_version == '3':
    serialized_manifest = emit_manifest_v3(labels, args.files, args.flat)
  else:
    raise Exception('manifest version "{}" is not supported'.format(args.schema_version))
  if args.output:
    with open(args.output, 'w') as output_file:
      output_file.write(serialized_manifest)
  else:
    sys.stdout.write(serialized_manifest)

if __name__ == '__main__':
  main()