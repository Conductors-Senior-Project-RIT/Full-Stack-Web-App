#!/bin/bash

# Loads test environment
set -a              # Auto-export all variables
source .env.test     # Load .env.test file
set +a              # Turn off auto-export

# running ./run_test.sh is equivalent to "python3 -m unittest ..." and you can pass in any arguments afterwards thanks to $@

folder="reports/tests/run_$(date '+%Y-%m-%d_%H-%M-%S')"
mkdir -p "$folder"
pytest backend/test/ --md-report --md-report-output "$folder/test_report.md" > "$folder/test_output.log"