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

from typing import Iterable
import logging
import convention

def from_files(convention_files: Iterable[str],
               user_paths: Iterable[str] = None):
  """Returns a new registry instantiated from the convention_files.

  Each convention gets passed the user_paths.
  """
  if not user_paths:
    user_paths = []
  registry = Registry()
  for filename in convention_files:
    logging.info('Reading config file "{}"'.format(filename))
    with open(filename) as config:
      registry.configure(config.read(), user_paths)

  convention.generate_environments(['lang_region', 'cloud', 'foobar'], user_paths)
  return registry

class Registry:
  """Stores the registered test execution environments."""

  def __init__(self):
    self.envs = {}

  def add_environment(self, environment):
    """Instantiates and stores a new testenv.Base with the given parameters.

    This function is primarily meant to be called by user-provided init code.
    """
    self.envs[environment.name()] = environment

  def configure(self, code, user_paths: Iterable[str]):
    symbols = {
        'register_test_environment': self.add_environment,
        'user_paths': user_paths.copy(),
    }
    exec(code, symbols)

  def get_names(self):
    """Returns the names of all the registered environments."""
    return list(self.envs.keys())

  def list(self):
    """Return all the registered environments."""
    return self.envs.values()
