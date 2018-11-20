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
  def __init__(self, call, args, kwargs):
    self.args = args
    self.kwargs = kwargs
    self.full = call
    self.service = None
    self.version = None
    self.rpc = None
    self.sample=None

    # parse the call into parts
    call_parts = call.split(':')
    if len(call_parts) > 2:
      raise ValueError('cannot parse call "{}"'.format(call))

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
