#!/bin/bash
set -exu -o pipefail
python -m unittest discover -s test/test_logic --verbose