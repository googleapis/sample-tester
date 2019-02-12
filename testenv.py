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

import logging
from typing import Iterable
import inspect


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
  return registry


class BaseTestEnvironment:

  def __init__(self, name='#BaseTestEnvironment', description=''):
    self._name = name
    self._description = description

  def name(self):
    return self._name

  def setup(self):
    logging.info('{}: setup'.format(self._name))

  def teardown(self):
    logging.info('{}: teardown'.format(self._name))

  def get_call(self, *args, **kwargs):
    logging.fatal(
        'get_call() invoked on BaseTestEnvironment (should be overridden)')


class Registry:
  """Stores the registered test execution environments."""

  def __init__(self):
    self.envs = {}

  def add_environment(self, environment):
    """Instantiates and stores a new BaseTestEnvironment with the given parameters.

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


def process_args(*args, **kwargs):
  """returns a pair (artifact name, arg invocation)"""
  positional_kwargs = []
  named_kwargs = []
  for name in kwargs:
    if name.startswith('_'):
      positional_kwargs.append(name)
    else:
      named_kwargs.append(name)
      positional_kwargs.sort()
      named_kwargs.sort()

  cmd_args = []
  for name in named_kwargs:
    cmd_args.append('--{}={}'.format(name, quote(kwargs[name])))
  for name in positional_kwargs:
    cmd_args.append(quote(kwargs[name]))

  cmd_args.extend([quote(a) for a in args[1:]])
  cli_arguments = ' '.join(cmd_args)
  return args[0], cli_arguments


def quote(s: str):
  return '"{}"'.format(s)
