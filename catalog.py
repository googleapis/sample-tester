import io
import logging
from typing import Iterable
import os.path
import yaml

class SampleCatalog:
  """Maintains a sample catalog from catalog files output by generator"""

  def __init__(self):
    self.interpreter = {"1": self.parse_catalog_v1}

    # by_label[language][label_type][label_value] = [metadata, metadata, ...]
    # eg by_label["python"]["path"]["/tmp/artifact"] = [ artifact1meta ]
    # eg by_label["python"]["region_tag"]["analyze_sentiment"] = [ sentiment_john_meta, sentiment_mary_meta ]
    self.by_label = {}


  def read_files(self, *files: str):
    return self.read_sources([(name, lambda: open(name, 'r')) for name in files])

  def read_strings(self, *sources: str):
    return self.read_sources([("string-{}".format(idx), lambda:io.StringIO(content)) for idx, content in enumerate(sources) if len(content) > 0])

  def read_sources(self, sources):
    """
    Read a sample catalog

    Start with:
    ```
      version: 1
      sample_sets:
        language: python
        base_dir:  some/path
        samples:
          "artifact":
            region_tag: tag_name
            canonical: name



  Eventually:
        sample_sets:
        - language: python
          canonical_name: Google.Cloud.Language.v1
          base_dir: MY/PYTHON/SAMPLES/DIR
          samples:
            "speech_v1_recognize_mary": recognize/recognize_mary.py
            "speech_v1_recognize_john": recognize/recognize_john.py

    """
    err_no_version = []
    err_no_interpreter = []
    sources_read = []
    for filename, opener in sources:
      logging.info('Reading catalog "{}"'.format(filename))
      with opener() as stream:
        catalog = yaml.load(stream)
        if not catalog:
          continue
        sources_read.append(filename)

        version = catalog.get('version')
        if version is None:
          err_no_version.append(filename)
          continue
        interpreter = self.interpreter.get(str(version))
        if not interpreter:
          err_no_interpreter.append(filename)
          continue

        try:
          interpreter(catalog)
        except Exception as e:
          logging.error('Error parsing catalog file "{}": {}'.format(filename, e))
          raise

    error = []
    if len(err_no_version) > 0:
      error.append('no version specified in catalog sources: "{}"'.format('", "'.join(err_no_version,)))
    if len(err_no_interpreter) > 0:
      error.append('invalid version specified in catalog sources: "{}"'.format('", "'.join(err_no_interpreter)))
    if len(error) > 0:
      error_msg = 'error reading catalog data:\n {}'.format('\n'.join(error))
      logging.error(error_msg)
      raise Exception(error_msg)
    return sources_read

  def parse_catalog_v1(self, input):
    for sample_set in input.get("sample_sets"):
      language = sample_set.get("language","")
      base_dir = sample_set.get("base_dir", "")
      language_catalog = get_or_create(self.by_label, language, {})

      all_samples = sample_set.get("samples", {})
      for path, metadata in all_samples.items():
        full_path = os.path.join(base_dir, path)
        metadata["path"] = full_path

        for label_type, label_value in metadata.items():
          type_catalog = get_or_create(language_catalog, label_type, {})
          catalog_entry = get_or_create(type_catalog, label_value, [])
          catalog_entry.append(metadata)

        logging.info('read "{}"'.format(full_path))

  def get(self, language, label_type, label_value):
    """Returns the list of values associated with label_type, label_value"""
    try:
      return self.by_label[language][label_type][label_value]
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
