import io
import logging
from typing import Iterable
import os.path
import yaml

class Manifest:
  """Maintains a manifest of auto-generated sample artifacts."""
  VERSION_KEY = "version"
  SETS_KEY = "_sets"
  ELEMENTS_KEY = "_items"


  def __init__(self, *indices: str):
    self.interpreter = {"1": self.parse_manifest_v1}

    # tags[key1][key2]...[keyn] == [metadata, metadata, ...]
    # eg with self.indices == ["language", "region_tag"]:
    #    tags["python"]["analyze_sentiment"] = [ sentiment_john_meta, sentiment_mary_meta ]
    self.tags = {}

    self.indices = indices or [None]

  def read_files(self, *files: str):
    self.read_sources(files_to_yaml(*files))

  def read_strings(self, *sources: str):
    self.read_sources(strings_to_yaml(*sources))

  def read_sources(self, sources):
    """ Reads a sample manifest.

    Args:
      sources: An iterable of (name, manifest) pairs

    Returns:
      the list of sources successfully read
    """
    err_no_version = []
    err_no_interpreter = []
    sources_read = []
    for name, manifest in sources:
      logging.info('reading manifest "{}"'.format(name))
      if not manifest:
        continue
      sources_read.append(name)

      version = manifest.get(self.VERSION_KEY)
      if version is None:
        err_no_version.append(name)
        continue
      interpreter = self.interpreter.get(str(version))
      if not interpreter:
        err_no_interpreter.append(name)
        continue

      try:
        interpreter(manifest)
      except Exception as e:
        logging.error('error parsing manifest file "{}": {}'.format(filename, e))
        raise

    error = []
    if len(err_no_version) > 0:
      error.append('no version specified in manifest sources: "{}"'.format('", "'.join(err_no_version,)))
    if len(err_no_interpreter) > 0:
      error.append('invalid version specified in manifest sources: "{}"'.format('", "'.join(err_no_interpreter)))
    if len(error) > 0:
      error_msg = 'error reading manifest data:\n {}'.format('\n'.join(error))
      logging.error(error_msg)
      raise Exception(error_msg)
    return sources_read

  def parse_manifest_v1(self, input):
    max_idx = len(self.indices) - 1

    for sample_set in input.get(self.SETS_KEY):

      # get the tag defaults/prefixes for this set
      set_values = sample_set.copy()
      set_values.pop(self.ELEMENTS_KEY, None)

      all_elements = sample_set.get(self.ELEMENTS_KEY, [])
      for element in all_elements:
        # add the needed defaults/prefixes to this element
        for key, value in set_values.items():
          element[key] = value + element.get(key, "")

        # store
        tags = self.tags
        for idx_num, idx_key in enumerate(self.indices):
          idx_value = element.get(idx_key, "")
          tags = get_or_create(tags,idx_value, [] if idx_num == max_idx else {})
        tags.append(element)

        logging.info('read "{}"'.format(element))

  def get(self, *keys, **filters):
    """Returns the list of values associated with label_type, label_value"""
    keys = keys or [None]
    try:
      tags = self.tags
      for idx in range(0, len(self.indices)):
        tags = tags[keys[idx]]
      return[element for element in tags if all(tag_filter in element.items() for tag_filter in filters.items())]
    except Exception as e:
      return None

  def get_one(self, *keys, **filters):
    """Returns the single value associated with label_type, label_value, or None otherwise"""
    values = self.get(*keys, **filters)
    if values is None or len(values) != 1:
      return None
    return values[0]


def get_or_create(d, key, empty_value):
  value = d.get(key)
  if value is None:
    value = empty_value
    d[key] = value
  return value


def files_to_yaml(*files: str):
  """ Reads sample manifests from files."""
  for name in files:
    with open(name, 'r') as stream:
      manifest = yaml.load(stream)
    yield (name, manifest)

def strings_to_yaml(*sources: str):
  """ Reads sample manifests from strings."""
  for data in sources:
    manifest = yaml.load(data)
    yield (name, manifest)
