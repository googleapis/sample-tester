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
import click
import io
import os
import re
import sys
import yaml

from collections import OrderedDict
from glob import glob
from textwrap import dedent
from typing import List
from yaml import Dumper
from yaml.representer import SafeRepresenter

ALL_LANGS = ["python", "java", "csharp", "nodejs", "ruby", "php", "go"]

# If not provided, BASEPATH_DEFAULT is the default value of BASEPATH_KEY for
# both factored and flat manifests.
BASEPATH_KEY = 'basepath'
BASEPATH_DEFAULT = '.'

### For manifest schema version 3

def emit_manifest_v3(tags, sample_globs, flat):
  if flat:
    return dump(create_flat_manifest_v3(tags, sample_globs))
  return create_factored_manifest_v3(tags, sample_globs)

def create_factored_manifest_v3(tags, sample_globs):
  """Creates a factored v3 manifest with the given top-level tags

  The `basepath` at the top level is the current working directory, and the
  `path` for each individual item is a reference to `basepath` followed by the
  glob resolution for that sample. The `sample` (ID) for each item is the value
  of the single region tag inside that sample file.
  """
  lines = ['type: manifest/samples',
           'schema_version: 3',
           'base: &common']
  forbid_names(tags, 'sample', 'path')

  have_basepath = False
  for name, value in tags:
    if name == BASEPATH_KEY:
      have_basepath = True
    lines.append("  {}: '{}'".format(name, value))
  if not have_basepath:
    lines.append("  {}: '{}'".format(BASEPATH_KEY, BASEPATH_DEFAULT))
  lines.append("samples:")
  for s in sample_globs:
    for sample_relative_path in glob(s, recursive=True):
      sample_absolute_path = os.path.join(os.getcwd(), sample_relative_path)
      lines.extend([
          "- <<: *common",
	  "  path: '{{{}}}/{}'".format(BASEPATH_KEY, sample_relative_path),
	  "  sample: '{}'".format(get_region_tag(sample_absolute_path))
          ])
  return '\n'.join(lines) + '\n'

def create_flat_manifest_v3(tags, sample_globs):
  """Creates a flat v3 manifest with the given tags

  The `path` for each individual item is the absolute path to the current
  working directory joined with the glob resolution for that sample. The
  `sample` (ID) for each item is the value of the single region tag inside that
  sample file.
  """
  forbid_names(tags, 'sample', 'path')
  items = []

  for s in sample_globs:
    for sample in glob(s, recursive=True):
      basepath = None
      entry_content = {}
      for name, value in tags:
        if name == BASEPATH_KEY:
          basepath = value
          continue
        entry_content[name] = value

      if not basepath:
        basepath = BASEPATH_DEFAULT
      sample_path = os.path.join(os.getcwd(), sample)

      entry = {
	  'path': os.path.join(basepath, sample),
	  'sample': get_region_tag(sample_path)
      }
      entry.update(entry_content)
      items.append(entry)

  manifest = OrderedDict()
  manifest["type"] = "manifest/samples"
  manifest["schema_version"] = 3
  manifest["samples"] = items
  return manifest


### For manifest schema version 2

def emit_manifest_v2(tags, sample_globs, flat):
  forbid_names(tags, 'sample', 'path')
  return dump(create_manifest_v2(tags, sample_globs))

def create_manifest_v2(tags, sample_globs):
  """Creates a v2 manifest with the given top-level tags

  The `path` at the top level is the current working directory, and the `path`
  for each individual item is the glob resolution for that sample. The `sample` (ID)
  for each item is the value of the single region tag inside that sample file.
  """
  manifest = OrderedDict()
  manifest['version'] = 2
  manifest['sets'] = []
  basepath = None

  environment = OrderedDict()
  for name, value in tags:
    if name == BASEPATH_KEY:
      basepath = value
      continue
    # adjust for backward compatibility
    if name == 'env':
      if value not in ALL_LANGS:
        sys.exit('Unrecognized language "{}": env should be one of {}'
                 .format(value, ALL_LANGS))
      name = 'environment'
    environment[name] = value

  if not basepath:
    basepath = BASEPATH_DEFAULT
  environment['path'] = "{}/".format(basepath)
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

### Helpers

def forbid_names(tags, *forbidden_names):
  """Raises an exception if any name in `tags` is in `forbidden`"""
  found = []
  for name, value in tags:
    if name in forbidden_names:
      found.append(name)
  if found:
    raise TagNameError('the following tag names are reserved because ' +
                         'they are auto-generated, given the other options ' +
                         'specified: {}'
                         .format(' '.join(['"{}"'.format(f) for f in found])))

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


class TagNameError(Exception):
  pass

### YAML helpers

def dict_representer(dumper, data):
  return dumper.represent_dict(data.items())

def dump(manifest):
  Dumper.add_representer(OrderedDict, dict_representer)
  Dumper.add_representer(str,
                         SafeRepresenter.represent_str)
  return yaml.dump(manifest, Dumper=Dumper, default_flow_style=False)

def parse_files_and_tags(params: List[str]) -> (List[str], List[str]):
  '''Obtains a list of files and a list of tag key/value pairs CLI args.

  This is a helper function for main to process the files_and_tags argument.
  '''
  files = []
  tags = []
  tag_prefix='--'
  tag_prefix_len=len(tag_prefix)

  for current in params:
    if current.startswith(tag_prefix):
      tag_parts = current[tag_prefix_len:].split('=', 1)
      tag_key = tag_parts[0]
      tag_value = tag_parts[1] if len(tag_parts) > 1 else ''
      tags.append((tag_key, tag_value))
    else:
      files.append(current)
  return (files, tags)


# Emitter functions indexed by schema version
registered_emitters= {
    '2': emit_manifest_v2,
    '3': emit_manifest_v3
}

@click.command(context_settings=dict(ignore_unknown_options=True))
@click.option('--schema_version',
              type=click.Choice(list(registered_emitters.keys())),
              default='3',
              help='schema version to use in the generated manifest')
@click.option('--output',
              type=click.Path(exists=False, allow_dash=True, writable=True),
              default='-',
              help='the name of the output file; `-` will output to stdout.')
@click.option('--flat', default=False,
              help=dedent('''\
                          whether to list all tags for each item, even if
                          this leads to duplicate YAML structures'''))
@click.argument('files_and_tags', nargs=-1, type=click.UNPROCESSED)
def main(schema_version: str, output: str, flat: bool, files_and_tags: List[str]):
  '''Generate manifest files for samples already on disk.

  This tool generates manifest files (for use in sample-tester) purely from
  existing sample artifacts already on disk. Each entry within the manifest file
  corresponds to a specific sample file on disk and lists the path to that file
  and the region tag occurring within that file. Any number of arbitrary
  key/value pairs can be specified and will be applied to all samples listed in
  the manifest.

  All samples have "path" tags relative to the directory whence this is run,
  prepended with the value/inclusion of the "basepath" tag. The value of
  "basepath" in turn comes from whatever value is specified via
  "--basepath=xxx", or defaults to "." otherwise. To provide absolute
  directories in the manifest, pass "--basepath=$(pwd)" to this tool.

  FILES_AND_TAGS is a sequence of double-dash-prefixed key-value pairs,
  representing tags to include in the manifest, and undashed filenames; order is
  not relevant. For example:

    --name=basic_sample --bin=python /my/dir/sample.py --status=beta
  '''
  try:
    sample_files, tags = parse_files_and_tags(list(files_and_tags))

    serialized_manifest = registered_emitters[schema_version](tags, sample_files, flat)

    if output != '-':
      with open(output, 'w') as output_file:
        output_file.write(serialized_manifest)
    else:
      sys.stdout.write(serialized_manifest)
  except TagNameError as e:
    print(f"ERROR: {e}")
    sys.exit(2)
