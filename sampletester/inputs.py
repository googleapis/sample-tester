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

import logging
import os

from sampletester import parser

from sampletester.sample_manifest import SCHEMA_TYPE_VALUE as MANIFEST_TYPE
from sampletester.testplan import SCHEMA_TYPE_VALUE as TESTPLAN_TYPE

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
      return MANIFEST_TYPE
    else:
      return TESTPLAN_TYPE
  else:
    msg = 'unknown file type: "{}"'.format(unknown_doc.path)
    logging.critical(msg)
    raise ValueError(msg)
