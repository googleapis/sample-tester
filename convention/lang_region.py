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

from sample_manifest import Manifest
import testenv

import glob
import logging
from typing import Iterable

LANGUAGE_KEY = 'language'
BINARY_KEY = 'bin'
REGION_KEY = 'region_tag'


class ManifestEnvironment(testenv.Base):
  """Sets up a manifest-derived Base for a single language.

  All artifacts with the same LANGUAGE_KEY are grouped in an instance of this
  class. Artifacts may also have a BINARY_KEY to denote how to run the artifact,
  if it is not executable.
  """

  def __init__(self, name: str, description: str, manifest: Manifest,
               indices: Iterable[str]):
    super().__init__(name, description)
    self.manifest = manifest
    self.const_indices = indices

  def get_call(self, *args, **kwargs):
    full_call, cli_args = testenv.process_args(*args, **kwargs)

    if '/' in full_call:
      artifact = full_call
    else:
      indices = self.const_indices.copy()
      indices.extend(full_call.split(' '))
      try:
        artifact = self.manifest.get_one(*indices)  # wrap exception?
      except Exception as e:
        raise Exception('object "{}" not defined: {}'.format(indices, e))
      try:
        bin = artifact.get(BINARY_KEY, '')
        artifact = ' '.join([bin, artifact['path']])
      except Exception as e:
        raise Exception('object "{}" does not contain "path": {}'.format(
            indices, e))
    return '{} {}'.format(artifact, cli_args)

  def adjust_suite_name(self, name):
    return self.adjust_name(name)

  def adjust_case_name(self, name):
    return self.adjust_name(name)

  def adjust_name(self, name):
    return '{}:{}'.format(name, ':'.join(self.const_indices))


all_manifests = []
languages = []
environments = []
def test_environments(manifest_paths):
    for path in manifest_paths:
      all_manifests.extend(
          glob.glob(path)
      )  # can do this?: _ = [a_m.extend(g.g(path)) for path in manifest_paths]
    manifest = Manifest(LANGUAGE_KEY, REGION_KEY) # read only, so don't need a copy
    manifest.read_files(*all_manifests)
    manifest.index()
    languages = manifest.get_keys()
    if len(languages) == 0:
      languages = ['(nolang)']
    for language in languages:
      description = 'Language, region_tags:{}'.format(language)
      name = language
      env  = ManifestEnvironment(name, description, manifest,
                                     [language])
      environments.append(env)
    logging.info('convention "lang_region" generated environments: {}'.format([env.name() for env in environments]))
    return environments
