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

import local_env as e
import test_v1
import test_v2

parser = argparse.ArgumentParser()
parser.add_argument('-1', '--v1', help='use lbaas v1 api')
parser.add_argument('-2', '--v2', help='use lbaas v2 api')
parser.add_argument('--pull-data', help='fetch traffic through LB VIP')
parser.parse_args()

if parser.v1:
    test_v1.run_tests(parser.pull_data)

if parser.v2:
    test_v2.run_tests(parser.pull_data)
