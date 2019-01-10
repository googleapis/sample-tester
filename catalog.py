import os.path
import yaml

class SampleCatalog:
  """Maintains a sample catalog from catalog files output by generator"""

  def __init__(self):
    self.interpreter = {"v1": self.parse_catalog_v1}

    # by_label[label_type][label_value] = [metadata, metadata, ...]
    # eg by_label["path"]["/tmp/artifact"] = [ artifact1meta ]
    # eg by_label["region_tag"]["analyze_sentiment"] = [ sentiment_john_meta, sentiment_mary_meta ]
    self.by_label = {}


  def read_files(self, files: Iterable[str]):
    self.read_sources([(name, lambda _: open(name, 'r')) for name in files])

  def read_strings(self, sources: Iterable[str]):
    self.read_sources([(idx, lambda _:content) for content in sources])

  def read_sources(self, files: Iterable[str]):
    """
    Read a sample catalog

  Start with:
    version: 1
    sample_sets:
    - language: python
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
    for filename, opener in sources:
      logging.info('Reading catalog "{}"'.format(filename))
      with opener() as stream:
        catalog = yaml.load(stream)
        version = catalog.get("version")
        if not version:
          err_no_version.append(filename)
          continue
        interpreter = this.interpreter.get(version)
        if not interpreter:
          err_no_interpreter.append(filename)

        try:
          interpreter(catalog)
        except Exception as e:
          logging.error('Error parsing catalog file "{}": {}'.format(filename, e))
          raise

    error = []
    if len(err_no_version) > 0:
      error.append('no version specified in catalog sources: "{}"'.format(string.join(err_no_version,'", "')))
    if len(err_no_interpreter) > 0:
      error.append('invalid version specified in catalog sources: "{}"'.format(string.join(err_no_interpreter,'", "')))
    if len(error) > 0:
      error_msg = 'error reading catalog data:\n {}'.format(string.join(error,'\n'))
      logging.error(error_msg)
      raise Exception(error_msg)

  def parse_catalog_v1(self, input):
    for sample_set in input.get("sample_sets"):
      language = sample_set["language"]
      base_dir = sample_set.get("base_dir", "")
      all_samples = input.get("samples", {}):
      for path, metadata in all_samples.items():
        full_path = os.path.join(path)
        meta_data["path"] = full_path

        for label_type, label_value in metadata:
          type_catalog = get_or_create(self.by_label, label_type, {})
          catalog_entry = get_or_create(type_catalog, label_value, [])
          catalog_entry.append(meta_data)

        logging.info('read "{}"'.format(full_path))

  def get(self, label_type, label_name):
    """Returns the list of values associated with label_type, label_name"""
    try:
      return self.by_label[label_type][label_value]
    except Exception as e:
      return None

  def get_one(self, label_type, label_name):
    """Returns the single value associated with label_type, label_name, or None otherwise"""
    values = self.get(label_type, label_name)
    if values is None or len(values) != 1:
      return None
    return values[0]


def get_or_create(d, key, empty_value):
  value = d.get(key)
  if value is None:
    value = empty_value
    d[key] = value
  return value
