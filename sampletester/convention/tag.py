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

# The value of INVOCATION_KEY in the manifest encodes how the given artifact is
# to be invoked. The value may contain the PLACEHOLDER_ARGS string below to
# indicate where command-line arguments are to be inserted at invocation time.
INVOCATION_KEY = 'invocation'

# The value of CHDIR_KEY in the manifest encodes the working directory the
# sample-tester should be in before invoking the artifact. If not specified, the
# current working directory is assumed.
CHDIR_KEY = 'chdir'

# This the special character that introduced placeholder strings for the
# INVOCATION_KEY value. To obtain this special character literally in the
# invocation (i.e. to escape it), insert it twice in succession.
PLACEHOLDER_CHAR = sample_manifest.RESERVED_SYMBOL_PREFIX

# The substring PLACEHOLDER_ARGS in the INVOCATION_KEY value gets replaced at
# run time with the arguments to be passed to the artifact.
PLACEHOLDER_ARGS = PLACEHOLDER_CHAR + 'args'

# (deprecated) The value of BINARY_KEY in the manifest denotes the program used
# to invoke the artifact in question if INVOCATION_KEY is not specified
BINARY_KEY = 'bin'

# The key to the artifact location on disk, which we will try to use to run the
# artifact if INVOCATION is not specified.
PATH_KEY = 'path'


class ManifestEnvironment(testenv.Base):
  """Sets up a manifest-derived Base for a single environment.

  All artifacts with the same ENVIRONMENT_KEY are grouped in an instance of this
  class.

  Artifacts may also have a value specified for the INVOCATION_KEY to denote how
  to run the artifact. This value may in turn use PLACEHOLDER_ARGS to denote
  where to insert the command-line arguments.

  If an artifact does not have an INVOCATION_KEY defined, but has a BINARY_KEY
  defined, the binary is executed with the value of PATH_KEY as its first
  argument, followed by the sample arguments. (Note that this usage is
  deprecated.)

  If neither INVOCATION_KEY nor BINARY_KEY are specified but PATH_KEY is
  specified, then path is executed with the artifact arguments.

  If none of INVOCATION_KEY, BINARY_KEY, nor PATH_KEY are specified, calls
  result in errors.

  The default invocation key can be overriden by passing a key-value pair
  (INVOCATION_KEY:  "new_invocation_key") in the manifest_options argument to init.

  Similarly, the default chdir key can be overriden by passing a key-value pair
  (CHDIR_KEY:  "new_chdir_key") in the manifest_options argument to init.
  """

  def __init__(self, name: str, description: str, manifest: sample_manifest.Manifest,
               indices: Iterable[str], testcase_settings=None, manifest_options=None):
    """Initializes ManifestEnvironment.

    Args:
      indices: the manifest index values that are not explicitly specified in
        each call but are assumed to correspond to initial indices before
        call-specific indices.
      testcase_settings: settings that change the fields expected in the
        testplan files
      manifest_options: settings that change how the manifest file is
        interpreted for this convention. Currently supported: a
        (INVOCATION_KEY: "new_invocation_key") key/value pair to
        configure which field is interpreted as the invocation format.
    """
    super().__init__(name, description)
    self.manifest = manifest
    self.const_indices = indices
    self._testcase_settings = testcase_settings
    self.manifest_options = (manifest_options
                             if manifest_options is not None else {})

  def get_symbol(self, symbol):
    """Returns the artifact manifest tag specified in `symbol`.

    `symbol` is interpreted as having the format `artifact:key`, and this method
    returns the value of the tag with key `key` listed for `artifact`. If `key`
    does not match any tag key for `artifact`, this returns the empty string.

    If `artifact` does not resolve to an artifact in the manifest, this raises
    an exception.

    If `key` is not specified, this method returns a serialized representation
    of all the tag key/value pairs for `artifact`.
    """
    parts = symbol.split(':')
    artifact, key = parts[0], parts[1] if len(parts) > 1 else None

    indices = self.const_indices.copy()
    indices.append(artifact)
    artifact = self.manifest.get_one(*indices)
    if not artifact:
      raise Exception('object "{}" not defined'.format(indices))

    if key:
      return artifact.get(key, '')

    # no key specified, so return all tags
    return str(artifact)

  def get_call(self, *args, **kwargs):
    full_call, cli_args = testenv.process_args(*args, **kwargs)

    indices = self.const_indices.copy()
    indices.extend(full_call.split(' '))
    artifact = self.manifest.get_one(*indices)
    if not artifact:
      raise Exception('object "{}" not defined'.format(indices))

    invocation_key = self.manifest_options.get(INVOCATION_KEY,
                                               INVOCATION_KEY)
    invocation = artifact.get(invocation_key, None)
    if not invocation:
      bin = artifact.get(BINARY_KEY, '')
      artifact_name = ' '.join([bin, artifact.get(PATH_KEY, '')]).strip()
      if len(artifact_name) == 0:
        raise Exception(
            'object "{}" must contain one of "{}", "bin", or "path": {}'
            .format(indices, invocation_key, artifact))
      invocation = '{} {}'.format(artifact_name, PLACEHOLDER_ARGS)

    chdir_key = self.manifest_options.get(CHDIR_KEY, CHDIR_KEY)
    chdir = artifact.get(chdir_key, None)
    return insert_into(invocation, (PLACEHOLDER_ARGS, cli_args)), chdir

  def adjust_suite_name(self, name):
    return self.adjust_name(name)

  def adjust_case_name(self, name):
    return self.adjust_name(name)

  def adjust_name(self, name):
    return '{}:{}'.format(name, ':'.join(self.const_indices))

  def get_testcase_settings(self):
    return self._testcase_settings

def insert_into(host: str, *replacements): #  placeholder: str, guest: str):
  """Returns a copy of host with all the specified replacements applied.

  Each element of `replacements` is a pair of a `placeholder` string (which must
  begin with PLACEHOLDER_CHAR) and a `subst` string to replace it. After
  freezing escaped instances of PLACEHOLDER_CHAR in `host`, each `placeholder`
  is then substituted by its `subst`. The previously frozen escaped instances of
  PLACEHOLDER_CHAR are then substituted with a literal PLACEHOLDER_CHAR, and the
  resulting string is then returned.
  """
  escaped_token = '\x10'  # arbitrary non-printable char to mark escaped spots
  escaped_inclusion = PLACEHOLDER_CHAR*2
  escaped = host.replace(escaped_inclusion, escaped_token)
  for placeholder, subst in replacements:
    if placeholder[0] != PLACEHOLDER_CHAR:
      raise InternalInvalidPlaceholderDefinition(
          'placeholder "{}" does not begin with PLACEHOLDER_CHAR "{}"'
          .format(placeholder, PLACEHOLDER_CHAR))
    escaped = escaped.replace(placeholder, subst)
  return escaped.replace(escaped_token, PLACEHOLDER_CHAR)


# A global record of all the manifest and environments created via all the calls to test_environments()
all_manifests = []
all_env_names = []
all_environments = []

def test_environments(manifest_paths, convention_parameters, manifest_options):
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

  manifest_options_dict = {}
  num_options = len(manifest_options) if manifest_options else 0
  manifest_options_dict[INVOCATION_KEY] = manifest_options[0] if num_options > 0 else INVOCATION_KEY
  manifest_options_dict[CHDIR_KEY] = manifest_options[1] if num_options > 1 else CHDIR_KEY

  environments = []
  for name in env_names:
    description = 'Tags by environment:{} {}'.format(name,
                                                     convention_parameters)
    env  = ManifestEnvironment(name, description, manifest, [name],
                               testcase_settings={'call.target': convention_parameters[0]},
                               manifest_options=manifest_options_dict)
    environments.append(env)
  logging.info('convention "tag" generated environments: {}'.format([env.name() for env in environments]))
  all_env_names.extend(env_names)
  all_environments.extend(environments)
  all_manifests.extend(manifest_files)
  return environments


class InternalInvalidPlaceholderDefinition(Exception):
  pass
