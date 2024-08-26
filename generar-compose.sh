#!/bin/bash

# Check if the required parameters are passed
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <filename> <number_of_clients>"
    exit 1
fi

python3 generate-compose.py $1 $2