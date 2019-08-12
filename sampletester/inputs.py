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

import glob
import itertools
import logging
import os
from functools import reduce
from typing import Set

from sampletester import parser
from sampletester.parser import SCHEMA_TYPE_ABSENT as UNKNOWN_TYPE
from sampletester.sample_manifest import SCHEMA as MANIFEST_SCHEMA
from sampletester.testplan import SCHEMA as TESTPLAN_SCHEMA


def untyped_yaml_resolver(unknown_doc: parser.Document) -> str :
  """Determines how `parser.IndexedDocs` should classify `unknown_doc`

  This is a resolver for parser.IndexedDocs, used to resolve YAML docs that did
  not have a type field and thus could not be automatically classified. This
  resolver resolves using the filename, for backward compatibility: files ending
  in `.manifest.yaml` are categorized as manifest files, and remaining YAML
  files are categorized as testplan files.
  """
  ext_split = os.path.splitext(unknown_doc.path)
  ext = ext_split[-1]
  if ext == ".yaml":
    prev_ext = os.path.splitext(ext_split[0])[-1]
    if prev_ext == ".manifest":
      return MANIFEST_SCHEMA.primary_type
    else:
      return TESTPLAN_SCHEMA.primary_type
  return UNKNOWN_TYPE


def index_docs(*file_patterns: str) -> parser.IndexedDocs:
  """Obtains manifests and testplans by indexing the specified paths or cwd.

  This function works in the following sequence:

  1. It attempts to obtain all the manifests and testplans contained in
  the globs in `file_patterns`.

  2. If either no manifest or no testplan is obtained this way:

    2.1 if any of the globs in `file_patterns` resolved to a directory, it does
        not search for any more files.

    2.2 if none of the globs in `file_patterns` resolved to a directory, it
        searches in all the paths under the cwd and registers the
        `file_patterns` matching the types not found in the previous step. In
        other words, if no manifests are found via the globs in `file_patterns`,
        it attempts to get manifests under the cwd, and similarly for testplans.

  Returns: the indexed docs of the files that were searched for.
  """
  explicit_paths = get_globbed(*file_patterns)
  explicit_directories = {path for path in explicit_paths
                          if os.path.isdir(path)}
  files_in_directories = get_globbed(*{f'{path}/**/*.yaml'
                                       for path in explicit_directories})
  explicit_paths |= files_in_directories

  indexed_explicit = create_indexed_docs(*explicit_paths)
  has_manifests = indexed_explicit.contains(MANIFEST_SCHEMA.primary_type)
  has_testplans = indexed_explicit.contains(TESTPLAN_SCHEMA.primary_type)

  if (has_manifests and has_testplans):
    # We have successfully found needed inputs already.
    return indexed_explicit

  if files_in_directories:
    # Because directories were specified, we use this as a signal to *not*
    # recurse into the cwd. The caller is responsible for reporting that one or
    # both of the needed file types is missing.
    return indexed_explicit

  implicit_files = get_globbed('**/*.yaml')
  indexed_implicit = create_indexed_docs(*implicit_files)
  if not has_testplans:
    indexed_explicit.add_documents(*indexed_implicit.of_type(TESTPLAN_SCHEMA.primary_type))
  if not has_manifests:
    indexed_explicit.add_documents(*indexed_implicit.of_type(MANIFEST_SCHEMA.primary_type))
  return indexed_explicit

def create_indexed_docs(*all_paths: Set[str]) -> parser.IndexedDocs:
  """Returns a parser.IndexedDocs that contains all documents in `all_paths`.

  This is a helper for `indexed_docs()`, and is also used heavily in tests.
  """
  indexed_docs = parser.IndexedDocs(resolver=untyped_yaml_resolver)
  indexed_docs.from_files(*all_paths)
  return indexed_docs


def get_globbed(*file_patterns: str) -> Set[str]:
  """Returns the set of files returned from globbing `file_patterns`"""
  return {filename
          for pattern in file_patterns
          for filename in glob.glob(pattern, recursive=True)}
