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

from .cloud import CloudRepos
from sampletester import parser

def test_environments(indexed_docs: parser.IndexedDocs,
                      convention_parameters,
                      _unused):
  files = [doc.path for doc in indexed_docs.of_type(parser.SCHEMA_TYPE_ABSENT)]
  num_params = 0 if convention_parameters is None else len(convention_parameters)
  if num_params != 0:
    raise Exception('expected no parameters to convention "cloud", got %d: %s'
                    .format(num_params, convention_parameters))
  return CloudRepos(files).test_environments()
