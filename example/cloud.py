from testenv import Call
import os
import re

print('*** in cloud.py!')

def setup():
  print('*** stub: cloud.py setup')

def teardown():
  print('*** stub: cloud.py teardown')

class PythonSamples:
  """
  Each instance of this processor contains a set of API client libraries in Python.
  """
  def __init__(self, path: str):
    self.path = path
    self.sample_rpc_paths = {}
    for api_dir in os.listdir(path):
      api_path = os.path.join(path,api_dir) # ...../googleapis/artman-genfiles/python/my-language-v1
      if not os.path.isdir(api_path):
        continue
      versioned_api = os.path.basename(api_path)  # my-language-v1
      parts = versioned_api.split('-')
      version_str = parts.pop() # v1
      api_str = '-'.join(parts) # my-language
      api_name = ''.join([word.capitalize() for word in parts])  # MyLanguage
      samples_rpc_dir = os.path.join(api_path, 'samples','google', 'cloud', '_'.join([api_str, version_str]), 'gapic') # ...../googleapis/artman-genfiles/python/my-language-v1/samples/google/cloud/my-language_v1/gapic
      key = 'Google.Cloud.{}.{}'.format(api_name, version_str) # Google.Cloud.MyLanguage.v1
      if len(os.listdir(samples_rpc_dir)) > 0:
        self.sample_rpc_paths[key] = samples_rpc_dir

  def get_call_mapper(self):
    lang = 'Python'
    def call_mapper(call: Call):
      key = '{}.{}'.format(call.service, call.version)
      if key not in self.sample_rpc_paths:
        raise ValueError('could not resolve call "{}": directory for "{}" not found'.format(call.full, key))

      sample_path=os.path.join(self.sample_rpc_paths[key], camel_to_lower_snake(call.rpc),call.sample+".py")
      interpreter = 'python3'
      command_line = '{} {} {}'.format(interpreter, sample_path, call.cli_arguments)
      return command_line

    return call_mapper

  def id(self):
    """
    Returns a unique ID for this processor instance
    """
    return "python:" + self.path

# from https://stackoverflow.com/a/1176023
first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')
def camel_to_lower_snake(input):
  s1 = first_cap_re.sub(r'\1_\2', input)
  return all_cap_re.sub(r'\1_\2', s1).lower()


class NoLangSamples:
  def get_call_mapper(self):
    def call_mapper(call: Call):
      raise ValueError('this should not have been reached')
    return call_mapper

  def id(self):
    return "nolang"

class CloudRepos:
  def __init__(self):
    self.lang_processor = {
        'python': PythonSamples,
    }
    self.repos = {}
    self.get_langs_and_repos(base_dirs or [os.getcwd()])

  def get_langs_and_repos(self, api_dirs):
    """
    For each element of api_dirs, registers each recognized sample repository
    that it finds under the language in which it is implemented.
    """
    for directory in api_dirs:
      self.get_artman_sample_dirs(directory)
    if len(self.repos) == 0:
      self.repos['nolang'] = NoLangSamples()
    for id, handler in self.repos.items():
      register_test_environment('google-cloud:'+id, setup, teardown, handler.get_call_mapper())

  def get_artman_sample_dirs(self, api_path):
    if not 'artman-genfiles' in os.listdir(api_path):
      return
    artman_path = os.path.join(api_path,'artman-genfiles')
    for lang_dir in os.listdir(artman_path):
      lang_path = os.path.join(artman_path, lang_dir)
      if not os.path.isdir(lang_path):
        continue
      lang = os.path.basename(lang_path)
      if not lang in self.lang_processor:
        continue
      processor = self.lang_processor[lang](lang_path)
      self.repos[processor.id()] = processor


cloud_repos = CloudRepos()
