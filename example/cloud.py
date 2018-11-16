print('*** in cloud.py!')

def stub0():
  print('*** in stub0!')

def stub5(a,b,c,d,e):
  print('*** in stub5!')

register_test_environment('example_env', stub0, stub0, stub5)
