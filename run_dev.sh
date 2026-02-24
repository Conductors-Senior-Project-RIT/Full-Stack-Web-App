#!/bin/bash

# Load development environment
if [ -f .env.dev ]; then
    set -a              # Auto-export all variables
    source .env.dev     # Load the file
    set +a              # Turn off auto-export
else
    echo "Error: .env.dev not found!"
    echo "Copy .env.example to .env.dev and configure it."
    exit 1
fi

flask --app backend:create_app run --debug
#flask run --debug