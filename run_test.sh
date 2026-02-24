#!/bin/bash

# Load test environment
if [ -f .env.test ]; then
    set -a              # Auto-export all variables
    source .env.test     # Load the file
    set +a              # Turn off auto-export
else
    echo "Error: .env.test not found!"
    echo "Copy .env.example to .env.test and configure it."
    exit 1
fi

# not 100% sure how we would run app to do testing i forgot lol