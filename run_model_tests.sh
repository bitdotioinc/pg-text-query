#!/bin/bash
set -exu -o pipefail
python -c "from test.test_model import runner; runner.main()"