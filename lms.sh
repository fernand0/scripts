#!/bin/bash

# LMS (Logitech Media Server) Control Script
# This script sends commands to an LMS server via netcat

# Default server configuration
SERVER_HOST="${LMS_HOST:-localhost}"
SERVER_PORT="${LMS_PORT:-9090}"

# Function to display usage information
usage() {
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Available commands:"
    echo "  wipecache          - Clear the server cache"
    echo "  rescan             - Rescan the music library"
    echo "  mixer volume <val> - Adjust volume (e.g., -2.5, +5, 50)"
    echo "  button <action>    - Send button command (jump_rew, jump_fwd, etc.)"
    echo "  pause              - Toggle pause/play"
    echo "  help               - Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  LMS_HOST - Server hostname (default: localhost)"
    echo "  LMS_PORT - Server port (default: 9090)"
    echo ""
    echo "Examples:"
    echo "  $0 wipecache"
    echo "  $0 rescan"
    echo "  $0 \"mixer volume -2.5\""
    echo "  $0 \"button jump_rew\""
    echo "  $0 pause"
    exit 1
}

# Function to send command to server
send_command() {
    local cmd="$1"

    # Check if netcat is available
    if ! command -v nc >/dev/null 2>&1 && ! command -v netcat >/dev/null 2>&1; then
        echo "Error: Neither 'nc' nor 'netcat' command found. Please install netcat."
        exit 1
    fi

    # Determine which netcat command to use
    local nc_cmd="nc"
    if ! command -v nc >/dev/null 2>&1; then
        nc_cmd="netcat"
    fi

    # Send command to server
    echo -e "$cmd\nexit\n" | $nc_cmd "$SERVER_HOST" "$SERVER_PORT"

    # Check if the command was successful
    if [ $? -ne 0 ]; then
        echo "Error: Failed to connect to $SERVER_HOST:$SERVER_PORT"
        exit 1
    fi
}

# Main script logic
if [ $# -eq 0 ]; then
    usage
fi

COMMAND="$1"

case "$COMMAND" in
    "wipecache")
        send_command "wipecache"
        ;;
    "rescan")
        send_command "rescan"
        ;;
    "mixer")
        if [ -z "$2" ] || [ -z "$3" ]; then
            echo "Error: Mixer command requires additional parameters"
            echo "Usage: $0 mixer volume <value>"
            exit 1
        fi
        send_command "mixer $2 $3"
        ;;
    "button")
        if [ -z "$2" ]; then
            echo "Error: Button command requires an action"
            echo "Usage: $0 button <action>"
            exit 1
        fi
        send_command "button $2"
        ;;
    "pause")
        send_command "pause"
        ;;
    "help"|"-h"|"--help")
        usage
        ;;
    *)
        # For custom commands, send as-is
        send_command "$COMMAND"
        ;;
esac