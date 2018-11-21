from testenv import Call
import os

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
      if not os.path.isdir(api_dir):
        continue
      logging.info('*** api_dir="{}"'.format(api_dir))
      versioned_api = os.path.basename(api_dir)
      parts = versioned_api.split('-')
      version_str = parts.pop()
      api_str = '-'.join(parts)
      api_name = ''.join([word.capitalize() for word in parts])
      samples_rpc_dir = os.path.join(api_dir, 'samples','google', 'cloud', '_'.join(api_str, version_str), 'gapic')
      if len(os.listdir(samples_rpc_dir)) > 0:
        self.sample_rpc_paths[api_name] = sample_rpc_dir

  def get_call_mapper(self):
    lang = 'Python'
    def call_mapper(call: Call):
      return '# convention-conforming call not implemented yet for {}'.format(lang)
    return call_mapper

  def id(self):
    """
    Returns a unique ID for this processor instance
    """
    return "python:" + self.path

class NoLangSamples:
  def get_call_mapper(self):
    def call_mapper(call: Call):
      raise ValueError('this should not have been reached')
    return call_mapper

  def id(self):
    return "nolang"

class CloudRepos:
  def __init__(self):
    self.lang_processors = {
        'python': PythonSamples,
    }
    self.repos = {}
    self.get_langs_and_repos(os.getcwd())

  def get_langs_and_repos(self, apis_dir):
    """
    Registers each recognized sample repository that it finds under the language
    in which it is implemented.
    """
    self.get_artman_sample_dirs(apis_dir)
    if len(self.repos) == 0:
      self.repos['nolang'] = NoLangSamples()
    for id, handler in self.repos.items():
      register_test_environment('google-cloud:'+id, setup, teardown, handler.get_call_mapper())

  def get_artman_sample_dirs(self, apis_dir):
    if not 'artman-genfiles' in os.listdir(apis_dir):
      return
    artman_dir = os.path.join(apis_dir,'artman-genfiles')
    for lang_dir in os.listdir(artman_dir):
      if not os.path.isdir(lang_dir):
        continue
      lang = os.path.basename(lang_dir)
      if not lang in self.lang_processors:
        continue
      processor = self.lang_processor[lang](lang_dir)
      logging.info('*** lang_dir="{}"'.format(lang_dir))
      self.repos[processor.id()] = processor


cloud_repos = CloudRepos()
