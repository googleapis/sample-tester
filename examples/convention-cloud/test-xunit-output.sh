#! /bin/bash

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

echo "Test sample-tester --xunit=file output"

xunit_file="$( mktemp /tmp/sample-tester.XXXXXXXXX )"

sample-tester --xunit="$xunit_file" --convention=cloud examples/convention-cloud/language.test.yaml examples/mock-samples/googleapis

xunit_xml="$( cat "$xunit_file" )"

for expected_text in                        \
  '<testsuite name="Language samples test'  \
  '<testcase name="Sentiment from text'     \
  '<system-out>'                            \
  'In setup &quot;hi&quot'                  \
  'Calling: python3 examples/mock-samples/' \
  'In teardown bye'                         \
;
do
  if ! grep --silent "$expected_text" "$xunit_file"; then
    echo "Assertion failed"
    echo "Expected $expected_text in:"
    echo "$xunit_xml"
    exit 1
  fi
done

echo "Tests passed"
