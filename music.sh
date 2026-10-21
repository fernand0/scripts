#!/bin/bash

# Check for dependencies
for cmd in whipper rsync ssh; do
  if ! command -v "$cmd" &> /dev/null; then
    echo "Error: $cmd is not installed." >&2
    exit 1
  fi
done

# Set the remote host and destination directory
REMOTE_HOST=${1:-"192.168.1.100"}
REMOTE_DEST_DIR=${2:-"/media/Music/"}

# Create a temporary directory
TEMP_DIR=$(mktemp -d)

# Cleanup function
cleanup() {
  echo "Cleaning up..."
  rm -rf "$TEMP_DIR"
}

# Register the cleanup function to be called on exit
trap cleanup EXIT

# Rip the CD
cd "$TEMP_DIR" || exit 1
whipper cd rip -C file -k --unknown || whipper cd -d /dev/sr1 rip -C file -k --unknown || { echo "Failed to rip CD"; exit 1; }

# whipper cd -d /dev/sr1 rip -C file  -k --unknown


# Find the most recently created directory
ultimo_directorio=$(ls -td "$TEMP_DIR"/*/ | head -n 1)
if [ -z "$ultimo_directorio" ]; then
  echo "Could not find the ripped CD directory"
  exit 1
fi

echo "Ripped CD directory: $ultimo_directorio"

# Find the most recently created album directory
ultimo_disco=$(ls -td "$ultimo_directorio"* | head -n 1)
if [ -z "$ultimo_disco" ]; then
  echo "Could not find the album directory"
  exit 1
fi

echo "Album directory: $ultimo_disco"

# Transfer the album to the remote host using rsync
rsync -avz --progress --rsync-path="sudo rsync" "$ultimo_disco" "$REMOTE_HOST:$REMOTE_DEST_DIR" || {
  echo "Failed to transfer album to remote host. Temporary files preserved in $TEMP_DIR"
  trap - EXIT
  exit 1
}

echo "Successfully ripped and transferred the CD to $REMOTE_HOST:$REMOTE_DEST_DIR."
