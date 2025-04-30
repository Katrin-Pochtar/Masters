#!/bin/bash

# Navigate to the script directory
cd "$(dirname "$0")"

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the upload script
python3 upload_stats.py

# Deactivate virtual environment if it was activated
if [ -d "venv" ]; then
    deactivate
fi 