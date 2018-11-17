print('*** in cloud.py!')

def setup():
  print('*** stub: cloud.py setup')

def teardown():
  print('*** stub: cloud.py teardown')

def quote(s: str):
  return '"{}"'.format(s)

# TODO(vchudnov): Make a testenv Call class that encapsulates the different parts of the call
def call_mapper(full_call, service, rpc, sample, args, kwargs):
  # TODO(vchudnov): Add support for calling convention

  positional_kwargs = []
  named_kwargs = []
  for name in kwargs:
    if name.startswith('_'):
      positional_kwargs.append(name)
    else:
      names.append(name)
  positional_kwargs.sort()
  named_kwargs.sort()

  cmd_args = []
  for name in named_kwargs:
    cmd_args.append('--{}={}'.format(name, quote(kwargs[name])))
  for name in positional_kwargs:
    cmd_args.append(quote(kwargs[name]))
  cmd_args.extend([quote(a) for a in args])

  return '{} {} # cloud.py'.format(full_call, ' '.join(cmd_args))

register_test_environment('example_env', setup, teardown, call_mapper)
