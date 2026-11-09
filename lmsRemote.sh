#!/bin/bash

# Configuration - could be moved to external config file
SSMAC="${SSMAC:-00:04:0C:00:00:10}"  # Allow override via environment variable
SSHOST="${SSHOST:-sbsserver}"

# Validate inputs
if [ $# -lt 1 ]; then
    echo "Usage: $0 <command>"
    echo "Example: $0 'play'"
    exit 1
fi

# Validate MAC address format
if [[ ! $SSMAC =~ ^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$ ]]; then
    echo "Invalid MAC address format: $SSMAC"
    exit 1
fi

# URL encode MAC address
MAC=$(echo -n "${SSMAC}" | tr '[:upper:]' '[:lower:]' | sed 's/:/%3A/g')

# Check if server is reachable
if ! exec 7<>"/dev/tcp/$SSHOST/9090" 2>/dev/null; then
    echo "Cannot connect to $SSHOST:9090"
    exit 1
fi

# Read credentials from environment variables or config file
USERID="${LMS_USERID:-}"
PASSWORD="${LMS_PASSWORD:-}"

if [ -z "$USERID" ] || [ -z "$PASSWORD" ]; then
    echo "LMS_USERID and LMS_PASSWORD environment variables must be set"
    exec 7<&-
    exec 7>&-
    exit 1
fi

# Send command to server
echo -e "login $USERID $PASSWORD\r" >&7
echo -e "$MAC $1\r" >&7
echo -e "exit\r" >&7

# Read response
RESPONSE=$(cat <&7)

# Close connection
exec 7<&-
exec 7>&-

# Output response
echo "$RESPONSE"
