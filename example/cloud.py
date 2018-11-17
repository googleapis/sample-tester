print('*** in cloud.py!')

def setup():
  print('*** stub: cloud.py setup')

def teardown():
  print('*** stub: cloud.py teardown')

def quote(s: str):
  return '"{}"'.format(s)

# TODO(vchudnov): Make a testenv Call class that encapsulates the different parts of the call
def call_mapper(full_call, service, rpc, sample, params):
  # TODO(vchudnov): Add support for calling convention

  positional_params = []
  named_params = []
  for name in params:
    if name.startswith('arg'):
      positional_params.append(name)
    else:
      names.append(name)
  positional_params.sort()
  named_params.sort()

  args = []
  for name in named_params:
    args.append('--{}={}'.format(name, quote(params[name])))
  for name in positional_params:
    args.append(quote(params[name]))

  return '{} {} # cloud.py'.format(full_call, ' '.join(args))

register_test_environment('example_env', setup, teardown, call_mapper)
