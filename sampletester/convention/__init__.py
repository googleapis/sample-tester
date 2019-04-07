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

import importlib
import logging
import os

DEFAULT="tag:sample"

__abs_file__ = os.path.abspath(__file__)
__abs_file_path__ = os.path.split(__abs_file__)[0]

# The list of environment creation functions for each of the various conventions
# we discover below.
environment_creators = {}

# We find all the conventions defined via modules and subpackages rooted in the
# current directory
all_files = [entry for entry in os.listdir(__abs_file_path__)
             if entry !='__init__.py' and entry != '__pycache__' and not entry.endswith('~')]
all_conventions = [os.path.splitext(os.path.basename(entry))[0] for entry in all_files]

# We register the environment creation function for each convention. Each such
# function has the name `test_environments` within the convention code.
for convention in all_conventions:
  module = importlib.import_module('.'+convention, package='sampletester.convention')
  if 'test_environments' in dir(module):
    logging.info('registering convention "{}"'.format(convention))
    environment_creators[convention] = module.test_environments

def generate_environments(requested_conventions, convention_args, files):
  """Generates the environments for the requested conventions with the given args.

  Note that a given convention may (and usually will) generate multiple
  environments, typically for running tests in multiple languages.

  Args:
    requested_conventions: A list of strings, each of which contains the
       name of a convention previously registered in `environment_creators`
    convention_args: A list of args to pass in its entirety to each convention
       in `requested_conventions`
    files: A list of files needed by the convention to instantiate environments.
  """
  all_environments = []
  for convention in requested_conventions:
    create_fn = environment_creators.get(convention, None)
    if create_fn is None:
      raise ValueError('convention "{}" not implemented'.format(convention))
    try:
      all_environments.extend(create_fn(files, convention_args))
    except Exception as ex:
      raise ValueError(
          'could not create test environments for convention "{}": {}'
          .format(convention, repr(ex)))
  return all_environments
