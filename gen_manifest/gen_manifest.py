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
import os
import sys
import re
import yaml

from collections import OrderedDict
from glob import glob
from yaml import Dumper
from yaml.representer import SafeRepresenter

ALL_LANGS = ["python", "java", "csharp", "nodejs", "ruby", "php", "go"]

def parse_args():
  parser = argparse.ArgumentParser()
  parser.add_argument('--schema_version', default='2',
                      help='schema version to use in the generated manifest')
  parser.add_argument('--output', required=True,
                      help='The name of the output file, should include the manifest.yaml` extension.')
  parser.add_argument('samples', nargs='*', help='Relative paths of sample files.')
  (args, labels) = parser.parse_known_args()
  labels = [(parts[0][2:], parts[1]) for parts in [label.split('=', 1) for label in labels]]
  return args, labels

### For manifest schema version 2

def create_manifest_v2(labels, samples):
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
  environment['__items__'] = path_sample_pairs_v2(samples)
  manifest['sets'].append(environment)
  return manifest


def path_sample_pairs_v2(samples):
  """Returns a list of path/ID pairs for each glob in `samples`"""
  items = []
  for s in samples:
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
  if args.schema_version != '2':
    raise Exception('only support manifest schema_version 2 at the moment')
  manifest = create_manifest_v2(labels, args.samples)
  serialized_manifest = dump(manifest)
  with open(args.output, 'w') as output_file:
    output_file.write(serialized_manifest)

if __name__ == '__main__':
  main()
