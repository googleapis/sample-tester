# move Call to a different module
from testenv import Call

print('*** in cloud.py!')

def setup():
  print('*** stub: cloud.py setup')

def teardown():
  print('*** stub: cloud.py teardown')

def quote(s: str):
  return '"{}"'.format(s)

def call_mapper(call: Call):
  # TODO(vchudnov): Add support for calling convention
  positional_kwargs = []
  named_kwargs = []
  for name in call.kwargs:
    if name.startswith('_'):
      positional_kwargs.append(name)
    else:
      named_kwargs.append(name)
  positional_kwargs.sort()
  named_kwargs.sort()

  cmd_args = []
  for name in named_kwargs:
    cmd_args.append('--{}={}'.format(name, quote(call.kwargs[name])))
  for name in positional_kwargs:
    cmd_args.append(quote(call.kwargs[name]))
  cmd_args.extend([quote(a) for a in call.args])

  return '{} {} # cloud.py'.format(call.full, ' '.join(cmd_args))

register_test_environment('example_env', setup, teardown, call_mapper)
