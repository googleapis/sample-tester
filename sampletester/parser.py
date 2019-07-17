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

import collections
import logging
import os
import yaml

from typing import Dict
from typing import List
from typing import Tuple

SCHEMA_TYPE_KEY = 'type'
SCHEMA_TYPE_ABSENT = '(no type)' # for indexing docs with no SCHEMA_TYPE_KEY
SCHEMA_TYPE_SEPARATOR = '/'

Document = collections.namedtuple('Document', ['path', 'obj'])

def from_files(*files: str) -> Dict[str, List[Document]]:
  docs = {}
  for file_name in files:
    file_path = os.path.abspath(file_name) # TODO: Do we want abspath here or in what's passed in?
    with open(file_path, 'r') as stream:
      content = stream.read()
      update_keyed_docs(docs, content, file_path)
  return docs

def from_strings(*sources: Tuple[str, str]) -> Dict[str, List[Document]]:
  docs = {}
  for description, content in sources:
      update_keyed_docs(docs, content, description)
  return docs


def update_keyed_docs(keyed_docs: Dict[str, List[Document]],
                      content,
                      file_name: str,
                      strict: bool = False)  -> Dict[str, List[Document]]:
  """Updates `keyed_docs` with all parsed YAML docs in `content`"""

  for doc in yaml.load_all(content):
    specified_type = doc.get(SCHEMA_TYPE_KEY, None)

    if not specified_type:
      msg = 'no top-level "{}" field specified'.format(SCHEMA_TYPE_KEY)
      if strict:
        raise SyntaxError(msg)
      logging.warning(msg)

    if not isinstance(specified_type, str):
      msg = ('top level "{}" field is not a string: {}'
             .format(SCHEMA_TYPE_KEY, specified_type))
      if strict:
        raise SyntaxError(msg)
      logging.warning(msg)
      specified_type = SCHEMA_TYPE_ABSENT

    type_name = specified_type.split(SCHEMA_TYPE_SEPARATOR, 1)[0]

    similar_docs = keyed_docs.get(type_name, [])
    if not similar_docs:
      keyed_docs[type_name] = similar_docs
    similar_docs.append(Document(file_name, doc))

class IndexedDocs(object):
  def __init__(self, strict=False, resolver=None):
    self.keyed_docs = {}
    self.strict = strict
    self.resolver = resolver

  def add(self, content:str, file_name: str):
    for doc in yaml.load_all(content):
      specified_type = doc.get(SCHEMA_TYPE_KEY, None)

      if not specified_type:
        msg = 'no top-level "{}" field specified'.format(SCHEMA_TYPE_KEY)
        if self.strict:
          raise SyntaxError(msg)
        logging.warning(msg)

      if not isinstance(specified_type, str):
        msg = ('top level "{}" field is not a string: {}'
               .format(SCHEMA_TYPE_KEY, specified_type))
        if self.strict:
          raise SyntaxError(msg)
        logging.warning(msg)
        specified_type = SCHEMA_TYPE_ABSENT

      type_name = specified_type.split(SCHEMA_TYPE_SEPARATOR, 1)[0]
      self._add_one(type_name, Document(file_name, doc))

      #self.resolve_uncategorized()

  def _add_one(self, type_name, doc):
    similar_docs = self.keyed_docs.get(type_name, [])
    if not similar_docs:
      self.keyed_docs[type_name] = similar_docs
    similar_docs.append(doc)

  def of_type(self, type_name: str) -> List[Document]:
    return self.keyed_docs.get(type_name, [])

  def resolve_uncategorized(self):
    # resolver should return the name of the type

    if not self.resolver:
      return

    unknowns = self.of_type(SCHEMA_TYPE_ABSENT)
    for idx, unknown_doc in enumerate(unknowns):
      new_type = self.resolver(unknown_doc)
      if not new_type or new_type == SCHEMA_TYPE_ABSENT:
        continue
      self._add_one(new_type, unknown_doc)
      unknowns[idx]=None
    self.keyed_docs[SCHEMA_TYPE_ABSENT] = [doc for doc in unknowns if doc]


class SyntaxError(Exception):
  pass
