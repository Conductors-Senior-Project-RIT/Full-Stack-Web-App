#!/bin/bash

# Load development environment
if [ -f .env.dev ]; then
    set -a              # Auto-export all variables
    source .env.dev     # Load the file
    set +a              # Turn off auto-export
else
    echo "Error: .env.dev not found!"
    echo "Copy .env.example to .env.dev and configure it."
fi

# wondering if i should add "$@" here like for the test script
flask --app 'backend:create_app("dev")' run --port 5000 --debug  

read -p "Press Enter to exit..."