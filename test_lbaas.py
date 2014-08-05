#!/usr/bin/env python
#
# Copyright 2014, Doug Wiegley (dougwig), A10 Networks
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import argparse
import sys

import test_v1
import test_v2

parser = argparse.ArgumentParser()
parser.add_argument('--v1', action="store_true", help='use lbaas v1 api')
parser.add_argument('--v2', action="store_true", help='use lbaas v2 api')
parser.add_argument('--pull-data', action="store_true",
                    help='fetch traffic through LB VIP')
parser.add_argument('--instance-network-name')
parser.add_argument('--lb-network-name')
parser.add_argument('member1')
parser.add_argument('member2')
parser.parse_args()

if parser.v1:
    test_v1.run_tests(parser)

if parser.v2:
    test_v2.run_tests(parser)

sys.exit(0)
