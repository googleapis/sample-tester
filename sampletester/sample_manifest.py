# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import io
import logging
import os.path
from typing import Iterable
import yaml


# This prefix marks symbols that have special semantics for the purposes of
# sample-tester, but that are not defined in the manifest schema itself.
RESERVED_SYMBOL_PREFIX = '@'


class Manifest:
  """Maintains a manifest of auto-generated sample artifacts.

  A manifest is a list of artifacts (read from one or more external sources,
  such as files or arrays). Each artifact on the list is, for the purposes of
  the manifest, simply a set of labels. A Manifest object knows nothing of the
  semantics of how it is used, but as an illustration, in sample-tester use
  cases, the following typically hold:
    - One of the labels for an artifact is the path to a sample on disk.
    - It is possible for more than one artifact to share the same set of labels,
      though typically some of the labels will be unique per artifact (eg sample
      ID, sample file path).

  A label contains a "label name" (a name of some category) and a "label value"
  (the value within that category). Neither values nor names need to be
  pre-defined.

  A manifest can be "indexed" by any number of labels. This is done by
  specifying the label name corresponding to the index keys. Look up by index
  (ie label value for the indexed label names) is O(1). Look up by a non-index
  key (label name/value pairs for non-indexed labels) is O(n) in the number of
  labels.

  For simplicity, we refer to the sequence of index label values (order
  determined by which the label names were configured) as the "keys", and the
  unordered list of un-indexed label name/value pairs as "filters".

  A typical look-up involves specifying the keys and filters.
  """

  # TODO: Change key to index in the doc above and usages below

  SCHEMA_TYPE_KEY = 'type'
  SCHEMA_TYPE_VALUE = 'manifest'
  SCHEMA_TYPE_SEPARATOR = '/'
  SCHEMA_VERSION_KEY = 'schema_version'

  # These values are deprecated and will go away once sampler tester stops
  # supporting manifest schema versions v1 and v2
  VERSION_KEY_v1v2 = 'version'
  SETS_KEY_v1v2 = 'sets'
  ELEMENTS_KEY_v1v2 = '__items__'

  def __init__(self, *indices: str):
    """Initializes manifest.

    Args:
      indices: An optional list of labels by which to index the manifest read in
        from various sources
    """
    self.interpreter = {
        '1': self.index_source_v1,
        '2': self.index_source_v2,
        '3': self.index_source_v3
    }

    # tags[key1][key2]...[keyn] == [metadata, metadata, ...]
    # eg with self.indices == ["language", "sample"]:
    #    tags["python"]["analyze_sentiment"] = [ sentiment_john_meta, sentiment_mary_meta ]
    self.tags = {}

    # sources is a list of (name, parsed-yaml, interpreter) tuples, set by
    # read_sources() and used by index()
    self.sources = []

    self.set_indices(*indices)

  def set_indices(self, *indices: str):
    self.indices = indices or [None]

  def read_files(self, *files: str):
    """Interprets files as YAML streams, each possibly containing multiple documents

    Args:
       files: any number of filenames to be parsed as YAML files
    """
    self.read_sources(files_to_yaml(*files))

  def read_strings(self, *sources: str):
    """Interprets strings as YAML streams, each possibly with multiple documents

    Args:
       str: any number of (label, yaml-string) pairs
    """
    self.read_sources(strings_to_yaml(*sources))

  def read_sources(self, sources):
    """Reads a sample manifest from a single YAML document.

    Args:
      sources: An iterable of (name, manifest) pairs. Here, `manifest` is a dict
        with a version key (`SCHEMA_VERSION_KEY` or `VERSION_KEY_v1v2`)
        and with the other keys structured as expected by the interpreter for
        the version specified as the value of the version key.

    Returns:
      the list of sources successfully read
    """
    err_no_version = []
    err_no_interpreter = []
    sources_read = []
    for name, manifest, implicit_tags in sources:
      logging.info('reading manifest "{}"'.format(name))
      if not manifest:
        continue
      sources_read.append(name)

      version = manifest.get(self.SCHEMA_VERSION_KEY)
      if version is None:
        version = manifest.get(self.VERSION_KEY_v1v2)
      if version is None:
        err_no_version.append(name)
        continue
      interpreter = self.interpreter.get(str(version))
      if not interpreter:
        err_no_interpreter.append(name)
        continue
      self.sources.append((name, manifest, interpreter, implicit_tags))

    error = []
    if len(err_no_version) > 0:
      error.append('no version specified in manifest sources: "{}"'.format(
          '", "'.join(err_no_version,)))
    if len(err_no_interpreter) > 0:
      error.append('invalid version specified in manifest sources: "{}"'.format(
          '", "'.join(err_no_interpreter)))
    if len(error) > 0:
      error_msg = 'error reading manifest data:\n {}'.format('\n'.join(error))
      logging.error(error_msg)
      raise Exception(error_msg)
    return sources_read

  def index(self):
    """Indexes all items in self.sources using appropriate interpreters."""
    self.tags = {}
    for name, manifest, interpreter, implicit_tags in self.sources:
      try:
        interpreter(manifest, implicit_tags)
      except Exception as e:
        logging.error('error parsing manifest source "{}": {}'.format(name, e))
        raise

  def index_source_v1(self, input, implicit_tags):
    self._index_elements(
        extend_all_with(implicit_tags,
                        check_tag_names(
                            get_flattened_elements_v1_v2(input))))

  def index_source_v2(self, input, implicit_tags):
    # v2 is an additive change over v1. It merely involves interpreting tags
    # included within other tags via curly braces
    self._index_elements(
        resolve_inclusions(
            extend_all_with(implicit_tags,
                            check_tag_names(
                                get_flattened_elements_v1_v2(input)))))

  def index_source_v3(self, input, implicit_tags):
    self._index_elements(
        resolve_inclusions(
            extend_all_with(implicit_tags,
                            check_tag_names(
                                get_elements_v3(input)))))

  def _index_elements(self, all_elements):
    if not all_elements:
      return

    max_idx = len(self.indices) - 1
    for element in all_elements:

      # first resolve all the indices, so that we end up with tags referring to the
      # non-index list
      tags = self.tags
      for idx_num, idx_key in enumerate(self.indices):
        idx_value = element.get(idx_key, '')
        tags = get_or_create(tags, idx_value,
                             [] if idx_num >= max_idx else {})
      tags.append(element) # appending to the  non-indexed list

    logging.info('indexed elements')

  def get_all_elements(self):
    """Generator that yields each element in the (indexed) manifest."""
    yield from self._get_element(self.tags, idx_num = 0)

  def _get_element(self, tags, idx_num):
    """Recursive helper function for get_all_elements.

    Traverses each index level to retrieve each list item individually.
    """
    idx_end = len(self.indices)
    if idx_num >= idx_end:
      # base case: we're done with indices, so just yield all the elements in the non-index list
      for element in tags:
        yield element
      return

    # recurse to the next index level
    for key, subtag  in tags.items():
      yield from self._get_element(subtag, idx_num+1)

  #TODO: add test
  def get_keys(self, *specified_keys):
    """Returns the keys at the next level after specified_keys have been resolved"""

    if self.indices == [None]:  # no indices
      return None
    if len(specified_keys) >= len(self.indices) - 1:
      return None
    tags = self.tags
    for idx in range(0, len(specified_keys)):
      tags = tags[keys[idx]]
    return list(tags.keys())

  def get(self, *keys, **filters):
    """Returns the list of artifacts associated with these keys and filters"""
    keys = keys or [None]
    try:
      tags = self.tags
      for idx in range(0, len(self.indices)):
        tags = tags[keys[idx]]
      return [element
              for element in tags
              if all(tag_filter in element.items()
                     for tag_filter in filters.items())]
    except Exception as e:
      return None

  def get_one(self, *keys, **filters):
    """Returns the single artifact associated with these keys and filters, or None otherwise"""
    values = self.get(*keys, **filters)
    if values is None or len(values) != 1:
      return None
    return values[0]


### Helpers for V3

def get_elements_v3(input):
  """Instantiates elements from file.

  Used by v3

  Args:
    input: the hierarchical manifest structure, typically as parsed from YAML
  """
  specified_type = input.get(Manifest.SCHEMA_TYPE_KEY, None)
  if not specified_type:
    raise SyntaxError('no top-level "{}" field specified'
                      .format(Manifest.SCHEMA_TYPE_KEY))
  if not isinstance(specified_type, str):
    raise SyntaxError('top level "{}" field is not a string: {}'
                      .format(Manifest.SCHEMA_TYPE_KEY, specified_type))

  type_parts = specified_type.split(Manifest.SCHEMA_TYPE_SEPARATOR)
  type_name = type_parts[0]
  if type_name != Manifest.SCHEMA_TYPE_VALUE:
    return None
  if len(type_parts) > 1:
    list_item = type_parts[1]
  if not list_item:
    raise SyntaxEror('missing item list name in "{}" field: "{}"'
                    .format(Manifest.SCHEMA_TYPE_KEY, specified_type))

  return input.get(list_item, [])


### Helpers for V1/V2

def get_flattened_elements_v1_v2(input):
  """Instantiates elements from file, applying any set-wide tags to each one

  Used by v1 and v2

  Args:
    input: the hierarchical manifest structure, typically as parsed from YAML
  """
  element_list=[]
  for sample_set in input.get(Manifest.SETS_KEY_v1v2):

    # Get the tag defaults/prefixes for this set
    set_common_values = sample_set.copy()
    set_common_values.pop(Manifest.ELEMENTS_KEY_v1v2, None)

    all_elements = sample_set.get(Manifest.ELEMENTS_KEY_v1v2, [])
    for element in all_elements:
      # Add the needed defaults/prefixes to this element
      for key, common_value in set_common_values.items():
        element[key] = common_value + element.get(key, '')
      element_list.append(element)
      logging.info('read "{}"'.format(element))
  return element_list


### Helpers for inclusions

class SyntaxError(Exception):
  def __init__(self, message):
    self.message = message

class CycleError(Exception):
  def __init__(self, message):
    self.message = message


def resolve_inclusions(all_elements):
  """Resolves tag inclusions in each element"""
  if not all_elements:
    return None
  for element in all_elements:
    resolve_element_inclusions(element)
  logging.info('resolved inclusions')
  return all_elements

def resolve_element_inclusions(element):
  """Resolves tag inclusions in element tags"""
  resolved=set()
  for tag_name in element.keys():
    resolve_tag_inclusion(element, tag_name, history=set(), resolved=resolved,
                          original_element = element.copy(), original_tag = tag_name)

def resolve_tag_inclusion (element, tag_name, history,
                           resolved, original_element, original_tag):
    """Recursive helper function for resolve_element_inclusions

    Args:
       element: the element whose tags we are to resolve
       tag_name: the tag to resolve in this invocation
       history: the tags that we have attempted to resolve in the process of
          resolving original_tag. Used to check for cycles.
       original_element: a copy of the element before any tag inclusions, for
          reporting errors
       original_tag: the original tag we are trying to resolve, for
          reporting errors
    """
    if tag_name in resolved:
      return element
    if tag_name in history:
      raise CycleError(
          'resolution of tag "{}"" creates a loop at included tag "{}" in item {}'
          .format(original_tag, tag_name, original_element))

    new_history = history.copy()
    new_history.add(tag_name)
    inclusion = Inclusions.determine(element[tag_name], element, tag_name)
    for child_tag_name in inclusion.needs.keys():
      resolve_tag_inclusion(element, child_tag_name, new_history, resolved,
                            original_element, original_tag)
    element[tag_name] = inclusion.resolve(element)
    resolved.add(tag_name)
    return element


class Inclusions:
  """Class to determine and perform the substitutions needed for one tag."""

  def __init__(self, parts):
    # a list of strings where each even-indexed string is a literal, and
    # each odd-index string is the name of a key. The inclusions are resolved
    # by substituting the values of the keys (with a map that is passed to
    # resolve())
    self.parts = parts

    # a map of keys to a list of indices in self.parts where that value of that
    # key should be substituted in. These indices are all odd numbers.
    self.needs = {}
    for idx in range(1,len(self.parts), 2):
      needed_where = get_or_create(self.needs, self.parts[idx], [])
      needed_where.append(idx)

  def resolve(self, values):
    """Resolves `self` by substituting inclusions with items from `values`."""
    for tag, locs in self.needs.items():
      for idx in locs:
        self.parts[idx] = values[tag]
    return ''.join(self.parts)

  def determine(value, element, tag_name):
    """Static method to instantiate Inclusions for tag_name in element"""
    find_position = 0
    write = ''
    parts = []

    # find all inclusions, taking care with escaped opening braces
    while True:
      open_idx = value.find('{', find_position)
      if open_idx == -1:
        parts.append(write+value[find_position:])
        break

      # we found open brace

      if open_idx >= len(value) - 1:  # need room for closing brace or escaped open
        raise SyntaxError(
            'no inclusion key for tag "{}" at position {} in item {}'
            .format(tag_name, open_idx, element))
      if value[open_idx+1] == '{':
        write = write + value[find_position:open_idx+1]
        find_position = open_idx + 2
        continue

      # this really is a tag inclusion

      parts.append(write + value[find_position:open_idx])

      close_idx = value.find('}', open_idx)
      if close_idx == -1:
        raise SyntaxError(
            'inclusion key starting at position {} is not terminated in '+
            'tag "{}" in item {}'
            .format(open_idx, tag_name, element))
      inclusion_name = value[open_idx+1:close_idx]
      if len(inclusion_name) == 0:
        raise SyntaxError(
            'inclusion key is empty at position {} for tag "{}" in item {}'
            .format(open_idx, tag_name, element))
      if inclusion_name.find('{') != -1:
        raise SyntaxError(
            'inclusion key "{}" cannot contain braces'.format(inclusion_name))
      parts.append(inclusion_name)

      find_position = close_idx+1
      write = ''

    # check that all closing braces are escaped in the literals
    for idx in range(0,len(parts),2):
      part = parts[idx]
      pos = -2
      while True:
        pos = part.find('}', pos+2)
        if pos == -1:
          break
        if (pos == len(part) - 1 or part[pos+1]!='}'):
          raise SyntaxError('closing brace not escaped')
        part=part[:pos+1]+part[pos+2:]
      parts[idx]=part.replace('}}','}')


    # everything is fine
    return Inclusions(parts)


### Helpers for implicit tags

IMPLICIT_TAG_SOURCE = '{}manifest_source'.format(RESERVED_SYMBOL_PREFIX)
IMPLICIT_TAG_DIR = '{}manifest_dir'.format(RESERVED_SYMBOL_PREFIX)

def create_implicit_tags(source='', dir=''):
  """Creates an implicit tag dict with the given values."""
  return {
      IMPLICIT_TAG_SOURCE: source,
      IMPLICIT_TAG_DIR: dir,
  }

def extend_all_with(src, dst):
  """Updates every map element of `dst` with the entries in `src`.

  This can be used to add a fixed set of implicit tags `src` to every element of
  a manifest `dst`.
  """
  if not src or not dst:
    return dst
  if not type(dst) in [list, tuple]:
    raise Exception('internal error: `dst` should be `list` or `tuple` (is {})'
                    .format(type(dst)))
  if type(src) is not dict:
    raise Exception('internal error: `src` should be `dict` is {}'
                    .format(type(src)))
  for element in dst:
    if type(element) is dict:
      element.update(src)

  return dst # to allow for composition


### Low-level helpers

def get_or_create(d, key, empty_value):
  """Returns the specified `key` from `d`, creating it if absent."""
  value = d.get(key)
  if value is None:
    value = empty_value
    d[key] = value
  return value


def files_to_yaml(*files: str):
  """Reads sample manifests from files.

  Args:
    sources: Any number of names of files, each containing one or more YAML
      documents.

  Yields:
    a tuple per YAML document in each file, each tuple containing the filename
    of its source file, the parsed YAML as a Python object, and the implicit
    tags (which have not yet been applied to the object). The implicit tags
    contain the filename itself and the directory of filename.  Note that none
    of YAML documents are guaranteed to be of the manifest type yet.
  """
  for file_name in files:
    # we delegate to strings_to_yaml below to have single code path for easier
    # testing and bug avoidance
    with open(file_name, 'r') as stream:
      content = stream.read()
      yield from strings_to_yaml(
          (file_name,
           content,
           create_implicit_tags(source=file_name, dir=os.path.dirname(file_name))))

def strings_to_yaml(*sources: str):
  """Reads sample manifests from strings.

  Args:
    sources: Any number of tuples, each containing the name of YAML source and
      the actual string representation of the YAML. An optional third element
      of each tuple is the set of implicit tags to add to the YAML; if not
      provided, just the name in the tuple is made into an implicit tag.

  Yields:
    a tuple per YAML document in each source, each tuple containing the name of
    its source, the parsed YAML as a Python object, and any implicit tags (which
    have not yet been applied to the object). Note that none of YAML documents
    are guaranteed to be of the manifest type yet.
  """
  for one_source in sources:
    name, data = one_source[0], one_source[1]
    implicit_tags = (one_source[2] if len(one_source) > 2
                     else create_implicit_tags(source=name))
    for manifest in yaml.load_all(data):
      yield (name, manifest, implicit_tags)

def check_tag_names(src):
  """Checks that all explicit tag names are valid."""
  if not src:
    return src
  invalid = [name
             for element in src
             for name in element.keys()
             if name.startswith(RESERVED_SYMBOL_PREFIX)]
  if invalid:
    raise SyntaxError('tag names may not begin with "{}": {}'
                      .format(RESERVED_SYMBOL_PREFIX,
                              ' '.join(['"{}"'.format(name) for name in invalid])))
  return src # to allow for composition
