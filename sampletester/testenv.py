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

class Base:

  def __init__(self, name='#Base', description=''):
    self._name = name
    self._description = description

  def name(self):
    return self._name

  def setup(self):
    logging.info('{}: setup'.format(self._name))

  def teardown(self):
    logging.info('{}: teardown'.format(self._name))

  def get_call(self, *args, **kwargs):
    """Translates the call arguments into a call to a binary on disk"""
    logging.fatal(
        'get_call() invoked on Base (should be overridden)')


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
