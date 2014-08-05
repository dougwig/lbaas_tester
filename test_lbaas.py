#!/usr/bin/env python

import argparse
import json
import os
import re
import requests
import subprocess
import tempfile
import time
import uuid

import test_v1
import test_v2

parser = argparse.ArgumentParser()
parser.add_argument('--v1', action="store_true", help='use lbaas v1 api')
parser.add_argument('--v2', action="store_true", help='use lbaas v2 api')
parser.add_argument('--pull-data', action="store_true", help='fetch traffic through LB VIP')
parser.add_argument('--instance-network-name')
parser.add_argument('--lb-network-name')
parser.add_argument('member1')
parser.add_argument('member2')
parser.parse_args()

if parser.v1:
    test_v1.run_tests(parser)

if parser.v2:
    test_v2.run_tests(parser)
