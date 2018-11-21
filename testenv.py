import logging
from typing import Iterable
import inspect

def from_files(config_files: Iterable[str]):
  """Returns a new registry instantiated from the config_files."""
  registry = Registry()
  for filename in config_files:
    logging.info('Reading config file "{}"'.format(filename))
    registry.configure(open(filename).read())
  return registry

class Registry:
  """Stores the registered test execution environments."""

  def __init__(self):
    self.envs = {}

  def add_environment(self, name: str, setup, teardown, call_mapper):
    """Instantiates and stores a new TestEnvironment with the given parameters.

    This function is primarily meant to be called by user-provided init code.
    """
    self.envs[name] = TestEnvironment(name, setup, teardown, call_mapper)

  def configure(self, code):
    symbols = {'register_test_environment': self.add_environment}
    exec(code, symbols)

  def get_names(self):
    return list(self.envs.keys())

  def list(self):
    return self.envs.values()



class TestEnvironment:
  def __init__(self, name, setup, teardown, call_mapper):
    logging.info('Creating environment "{}"'.format(name))
    self.name = name

    check_signatures(name,
                     ('setup', setup, 0),
                     ('teardown', teardown, 0),
                     ('call_mapper', call_mapper, 1))
    self.setup = setup
    self.teardown = teardown
    self.call_mapper = call_mapper

def check_signatures(name, *expected):
  msg = []
  for label, fn, nargs in expected:
    if not fn:
      msg.append('{} function is not set'.format(label))
      continue
    if not inspect.isfunction(fn) and not inspect.ismethod(fn):
      msg.append('{} function has not been provided a function'.format(label))
      continue
    actual_nargs = len(inspect.signature(fn).parameters)
    if actual_nargs != nargs:
      msg.append('{} function ("{}") has {} arguments, expected {}'.format(label, fn.__name__, actual_nargs, nargs))
  if len(msg) > 0:
    msg = 'Error setting up environment "{}": '.format(name) +  '; '.join(msg)
    logging.critical(msg)
    raise ValueError(msg)


class Call:
  def __init__(self, env, args, kwargs):
    self.args = args[1:]
    self.kwargs = kwargs
    self.full = args[0]
    self.service = None
    self.version = None
    self.rpc = None
    self.sample=None
    self.env = env

    # parse the call into parts
    call_parts = self.full.split(':')
    if len(call_parts) > 2:
      raise ValueError('cannot parse call "{}"'.format(self.full))

    if len(call_parts) == 1:
      return

    # Service[.Subservice ...].Version.RPC:sample
    self.sample = call_parts[1]
    rpc_parts = call_parts[0].split('.')
    if len(rpc_parts) > 0:
      self.rpc = rpc_parts.pop()
    if len(rpc_parts) > 0:
      self.version = rpc_parts.pop()
    if len(rpc_parts) > 0:
      self.service = '.'.join(rpc_parts)

  def cmd(self):
    """
    Resolves the binary that the current call resolves to under the given
    environment, and returns the fully qualified path to that binary.
    """
    positional_kwargs = []
    named_kwargs = []
    for name in self.kwargs:
      if name.startswith('_'):
        positional_kwargs.append(name)
      else:
        named_kwargs.append(name)
        positional_kwargs.sort()
        named_kwargs.sort()

    cmd_args = []
    for name in named_kwargs:
      cmd_args.append('--{}={}'.format(name, quote(self.kwargs[name])))
    for name in positional_kwargs:
      cmd_args.append(quote(self.kwargs[name]))
    cmd_args.extend([quote(a) for a in self.args])

    if not self.rpc:
      # this is a direct binary call
      return '{} {} # cloud.py from within {}'.format(self.full, ' '.join(cmd_args), self.env.name)

    return env.call_mapper(self)

def quote(s: str):
  return '"{}"'.format(s)
