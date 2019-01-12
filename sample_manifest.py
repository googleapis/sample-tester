import io
import logging
from typing import Iterable
import os.path
import yaml

class Manifest:
  """Maintains a manifest of auto-generated sample artifacts."""

  def __init__(self):
    self.interpreter = {"1": self.parse_manifest_v1}

    # tags[language][label_type][label_value] = [metadata, metadata, ...]
    # eg tags["python"]["path"]["/tmp/artifact"] = [ artifact1meta ]
    # eg tags["python"]["region_tag"]["analyze_sentiment"] = [ sentiment_john_meta, sentiment_mary_meta ]
    self.tags = {}


  def read_files(self, *files: str):
    """ Reads sample manifests from files."""
    return self.read_sources([(name, lambda: open(name, 'r')) for name in files])

  def read_strings(self, *sources: str):
    """ Reads sample manifests from strings."""
    return self.read_sources([("string-{}".format(idx), lambda:io.StringIO(content)) for idx, content in enumerate(sources) if len(content) > 0])

  def read_sources(self, sources):
    """ Reads a sample manifest."""
    err_no_version = []
    err_no_interpreter = []
    sources_read = []
    for filename, opener in sources:
      logging.info('Reading manifest "{}"'.format(filename))
      with opener() as stream:
        manifest = yaml.load(stream)
        if not manifest:
          continue
        sources_read.append(filename)

        version = manifest.get('version')
        if version is None:
          err_no_version.append(filename)
          continue
        interpreter = self.interpreter.get(str(version))
        if not interpreter:
          err_no_interpreter.append(filename)
          continue

        try:
          interpreter(manifest)
        except Exception as e:
          logging.error('Error parsing manifest file "{}": {}'.format(filename, e))
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
    for sample_set in input.get("sample_sets"):
      language = sample_set.get("language","")
      base_dir = sample_set.get("base_dir", "")
      language_manifest = get_or_create(self.tags, language, {})

      all_samples = sample_set.get("samples", {})
      for path, metadata in all_samples.items():
        full_path = os.path.join(base_dir, path)
        metadata["path"] = full_path

        for label_type, label_value in metadata.items():
          type_manifest = get_or_create(language_manifest, label_type, {})
          manifest_entry = get_or_create(type_manifest, label_value, [])
          manifest_entry.append(metadata)

        logging.info('read "{}"'.format(full_path))

  def get(self, language, label_type, label_value):
    """Returns the list of values associated with label_type, label_value"""
    try:
      return self.tags[language][label_type][label_value]
    except Exception as e:
      return None

  def get_one(self, language, label_type, label_value):
    """Returns the single value associated with label_type, label_value, or None otherwise"""
    values = self.get(language, label_type, label_value)
    if values is None or len(values) != 1:
      return None
    return values[0]


def get_or_create(d, key, empty_value):
  value = d.get(key)
  if value is None:
    value = empty_value
    d[key] = value
  return value
