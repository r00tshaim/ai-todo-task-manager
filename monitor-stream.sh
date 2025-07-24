#!/bin/bash

echo "Monitoring Redis streams for job updates..."

while true; do
    STREAMS=$(redis-cli -h localhost -p 6379 KEYS "job:*:stream")
    
    if [ ! -z "$STREAMS" ]; then
        echo "Active streams found:"
        echo "$STREAMS"
        echo "---"
        
        for stream in $STREAMS; do
            echo "Latest from $stream:"
            # Get the latest message ID
            LATEST_ID=$(redis-cli -h localhost -p 6379 XREVRANGE "$stream" + - COUNT 1 | head -n 1)
            if [ ! -z "$LATEST_ID" ]; then
                redis-cli -h localhost -p 6379 XRANGE "$stream" "$LATEST_ID" "$LATEST_ID"
            else
                echo "No messages in $stream"
            fi
            echo "---"
        done
    else
        echo "No active streams found"
    fi
    
    sleep 5
done