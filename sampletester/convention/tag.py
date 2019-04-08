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

import glob
import logging
from typing import Iterable

from sampletester import sample_manifest
from sampletester import testenv

# The value of ENVIRONMENT_KEY in the manifest is a human convenience used to
# group test suites for easier reporting. Its presence, absence, or value does
# not affect the actual execution of the tests since we do not currently support
# environment-specific set-up or tear-down.
ENVIRONMENT_KEY = 'environment'

# The value of BINARY_KEY in the manifest denotes the program used to invoke the
# artifact in question, and should be specified if the artifact is not itself
# executable.
BINARY_KEY = 'bin'


class ManifestEnvironment(testenv.Base):
  """Sets up a manifest-derived Base for a single environment.

  All artifacts with the same ENVIRONMENT_KEY are grouped in an instance of this
  class. Artifacts may also have a BINARY_KEY to denote how to run the artifact,
  if it is not executable.
  """

  def __init__(self, name: str, description: str, manifest: sample_manifest.Manifest,
               indices: Iterable[str], testcase_settings=None):
    """Initializes ManifestEnvironment.

    Args:
      indices: the manifest index values that are not explicitly specified in
        each call but are assumed to correspond to initial indices before
        call-specific indices.
    """
    super().__init__(name, description)
    self.manifest = manifest
    self.const_indices = indices
    self._testcase_settings = testcase_settings

  def get_call(self, *args, **kwargs):
    full_call, cli_args = testenv.process_args(*args, **kwargs)

    indices = self.const_indices.copy()
    indices.extend(full_call.split(' '))
    artifact = self.manifest.get_one(*indices)  # wrap exception?
    if not artifact:
      raise Exception('object "{}" not defined'.format(indices))
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

  def get_testcase_settings(self):
    return self._testcase_settings

# A global record of all the manifest and environments created via all the calls to test_environments()
all_manifests = []
all_env_names = []
all_environments = []

def test_environments(manifest_paths, convention_parameters):
  if convention_parameters is None:
    convention_parameters = []
  num_params = len(convention_parameters)
  if num_params < 1:
    raise Exception('expected at least 1 parameter to convention "tag", got %d: %s'
                    .format(num_params, convention_parameters))

  manifest_files = []
  for path in manifest_paths:
    manifest_files.extend(
        glob.glob(path)
    )  # can do this?: _ = [a_m.extend(g.g(path)) for path in manifest_paths]
  manifest = sample_manifest.Manifest(ENVIRONMENT_KEY, *convention_parameters) # read only, so don't need a copy
  manifest.read_files(*manifest_files)
  manifest.index()

  env_names = []
  env_names = manifest.get_keys()
  if len(env_names) == 0:
    env_names = ['(nolang)']

  environments = []
  for name in env_names:
    description = 'Tags by environment:{} {}'.format(name,
                                                     convention_parameters)
    env  = ManifestEnvironment(name, description, manifest, [name], testcase_settings={'call.target': convention_parameters[0]})
    environments.append(env)
  logging.info('convention "tag" generated environments: {}'.format([env.name() for env in environments]))
  all_env_names.extend(env_names)
  all_environments.extend(environments)
  all_manifests.extend(manifest_files)
  return environments
