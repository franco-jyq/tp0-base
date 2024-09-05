#!/bin/bash

NETWORK_NAME="testing_net"
SERVER_CONTAINER_NAME="server"
SERVER_IP="172.25.125.2"  
SERVER_PORT=12345         
MESSAGE="Hello, Echo Server!"
VERBOSE=0  


validate_server() {
    
    output=$(docker run --rm --network $NETWORK_NAME busybox sh -c "echo '$MESSAGE' | nc -w 5 server $SERVER_PORT")


    # Check if the output matches the expected echo
    if [ "$output" = "$MESSAGE" ]; then
        echo "action: test_echo_server | result: success"
    else
        echo "action: test_echo_server | result: fail"
    fi
}

validate_server