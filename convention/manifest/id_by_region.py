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

import testenv
import glob
from typing import Iterable
from sample_manifest import Manifest

LANGUAGE_KEY = 'language'
BINARY_KEY = 'bin'
REGION_KEY='region_tag'

class ManifestEnvironment(testenv.BaseTestEnvironment):
  """Sets up a manifest-derived BaseTestEnvironment for a single language.

  All artifacts with the same LANGUAGE_KEY are grouped in an instance of this
  class. Artifacts may also have a BINARY_KEY to denote how to run the artifact,
  if it is not executable.
  """

  def __init__(self, name: str, description:str, manifest: Manifest, indices: Iterable[str]):
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
        artifact = self.manifest.get_one(*indices) # wrap exception?
      except Exception as e:
        raise Exception('object "{}" not defined: {}'.format(indices, e))
      try:
        bin = artifact.get(BINARY_KEY, '')
        artifact = ' '.join([bin,artifact['path']])
      except Exception as e:
        raise Exception('object "{}" does not contain "path": {}'.format(indices, e))
    return '{} {}'.format(artifact, cli_args)

  def adjust_suite_name(self, name):
    return self.adjust_name(name)

  def adjust_case_name(self, name):
    return self.adjust_name(name)

  def adjust_name(self, name):
    return '{}:{}'.format(name, ':'.join(self.const_indices))



class LanguageRegionManifestEnvironmentProvider:
  def __init__(self, manifest_paths):
    all_manifests = []
    for path in manifest_paths:
      all_manifests.extend(glob.glob(path))  # can do this?: _ = [a_m.extend(g.g(path)) for path in manifest_paths]
    self.manifest = Manifest(LANGUAGE_KEY,REGION_KEY)
    self.manifest.read_files(*all_manifests)
    self.manifest.index()
    self.languages = self.manifest.get_keys()
    if len(self.languages) == 0:
      self.languages = ["(nolang)"]
    self.resolver={}
    for language in self.languages:
      description = 'Language, region_tags:{}'.format(language)
      name=language
      resolver = ManifestEnvironment(name, description, self.manifest, [language])
      self.resolver[language] = resolver
      register_test_environment(resolver)


resolver = LanguageRegionManifestEnvironmentProvider(user_paths)
