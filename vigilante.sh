#!/bin/bash
PID="${1:?Usage: $0 <PID>}"
while kill -0 "$PID" 2>/dev/null; do
  echo "Process $PID still running..."
  sleep 60
done
echo "Process $PID has finished"
