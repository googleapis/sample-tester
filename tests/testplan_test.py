#!/usr/bin/env python3
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

import unittest
from textwrap import dedent

from sampletester import parser
from sampletester import testplan


class TestTestPlan(unittest.TestCase):
  def setUp(self):
    config_yaml = [
      ("particles",
       dedent('''\
       type: test/samples
       schema_version: 1
       test:
         suites:
         - name: hadrons
           cases:
           - name: proton
           - name: neutron
         - name: leptons
           cases:
           - name: electron
           - name: muon
           - name: tauon
       ''')),
    ]
    self.config = parser.IndexedDocs()
    self.config.from_strings(*config_yaml)

  def test_suites_from_no_filter(self):
    test_plan = testplan.suites_from(self.config)

    selected_suites = {suite.name() for suite in test_plan if suite.selected()}
    selected_cases = {test_case.name()
                      for suite in test_plan
                      for test_case in suite.cases
                      if suite.selected() and test_case.selected()}
    self.assertEqual({'hadrons', 'leptons'}, selected_suites)
    self.assertEqual({'proton', 'neutron', 'electron', 'muon','tauon'}, selected_cases)

  def test_suites_from_filter_suites(self):
    test_plan = testplan.suites_from(self.config, suite_filter='adr')

    selected_suites = {suite.name() for suite in test_plan if suite.selected()}
    selected_cases = {test_case.name()
                      for suite in test_plan
                      for test_case in suite.cases
                      if suite.selected() and test_case.selected()}
    self.assertEqual({'hadrons'}, selected_suites)
    self.assertEqual({'proton', 'neutron'}, selected_cases)

  def test_suites_from_filter_cases(self):
    test_plan = testplan.suites_from(self.config, case_filter='tron')

    selected_suites = {suite.name() for suite in test_plan if suite.selected()}
    selected_cases = {test_case.name()
                      for suite in test_plan
                      for test_case in suite.cases
                      if suite.selected() and test_case.selected()}
    self.assertEqual({'hadrons', 'leptons'}, selected_suites)
    self.assertEqual({'neutron', 'electron'}, selected_cases)

  def test_suites_from_filter_suites_and_cases(self):
    test_plan = testplan.suites_from(self.config, suite_filter='adr', case_filter='tron')

    selected_suites = {suite.name() for suite in test_plan if suite.selected()}
    selected_cases = {test_case.name()
                      for suite in test_plan
                      for test_case in suite.cases
                      if suite.selected() and test_case.selected()}
    self.assertEqual({'hadrons'}, selected_suites)
    self.assertEqual({'neutron'}, selected_cases)
