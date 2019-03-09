#!/bin/bash
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

cd $(dirname "${BASH_SOURCE[0]}")
SAMPLE_DIRECTORY=${SAMPLE_DIRECTORY:-../../../../../python-docs-samples/vision/cloud-client/product_search}

pushd ${SAMPLE_DIRECTORY} >& /dev/null || { echo ">> Pretend call to create_product $@" ; exit 0 ; }
python3 ./product_management.py --project_id actools-sample-tester create_product "$@"
ret=$?
popd >& /dev/null
exit $ret
