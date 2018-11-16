print('*** in cloud.py!')

def setup():
  print('*** stub: cloud.py setup')

def teardown():
  print('*** stub: cloud.py teardown')

# TODO(vchudnov): Make a testenv Call class that encapsulates the different parts of the call
def call_mapper(full_call, service, rpc, sample, params):
  # TODO(vchudnov): Add support for calling convention
  return full_call + "  # cloud.py"

register_test_environment('example_env', setup, teardown, call_mapper)
