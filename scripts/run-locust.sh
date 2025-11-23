#!/bin/bash

HOST="${1:-http://localhost:8000}"
USERS="${2:-5}"
SPAWN_RATE="${3:-5}"

echo "Starting Locust Load Testing"
echo "Host: $HOST"
echo "Users: $USERS"
echo "Spawn Rate: $SPAWN_RATE/sec"
echo ""
echo "Open: http://localhost:8089"
echo ""

locust -f load-testing/locust/locustfile.py \
    --host=$HOST \
    --users=$USERS \
    --spawn-rate=$SPAWN_RATE