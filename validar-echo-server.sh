#!/bin/bash

NETWORK_NAME="tp0-base_testing_net"
SERVER_CONTAINER_NAME="server"
SERVER_IP="172.25.125.2"  
SERVER_PORT=12345         
MESSAGE="Hello, Echo Server!"
VERBOSE=0  

# Parse command-line options
while [[ "$1" != "" ]]; do
    case $1 in
        -v | --verbose ) 
            VERBOSE=1
            ;;
    esac
    shift
done

validate_server() {
    if [ $VERBOSE -eq 1 ]; then
        echo "Validating echo server..."
    fi

    output=$(docker run --rm --network $NETWORK_NAME busybox sh -c "echo '$MESSAGE' | nc -w 10 $SERVER_IP $SERVER_PORT")
    
    if [ $VERBOSE -eq 1 ]; then
        echo "Validation Output:"
        echo "$output"
    fi

    # Check if the output matches the expected echo
    if [ "$output" == "$MESSAGE" ]; then
        echo "action: test_echo_server | result: success"
    else
        echo "action: test_echo_server | result: fail"
    fi
}

validate_server