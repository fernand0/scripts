#!/bin/bash

# Configuration variables
home_bot="${BOT_HOME:-$HOME/usr/src/Python/deGitHub/botElectrico/}"
posts_dir="${POSTS_DIR:-docs/_posts/}"
tmp_dir="${TMP_DIR:-/tmp}"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >&2
}

# Error handling function
error_exit() {
    log "ERROR: $1"
    exit "${2:-1}"
}

# Function to safely execute git commands
git_safe() {
    log "Executing: git $*"
    if ! git "$@"; then
        error_exit "Git command failed: git $*"
    fi
}

# Set script options
set -euo pipefail  # Exit on error, undefined vars, and pipe failures

log "Starting postBotElectrico.sh..."

# Validate required directories
if [[ ! -d "$home_bot" ]]; then
    error_exit "Bot directory does not exist: $home_bot"
fi

# Change to the repository directory
cd "$home_bot" || error_exit "Could not change to repository directory: $home_bot"

# Verify it's a Git repository
if [[ ! -d ".git" ]]; then
    error_exit "Directory $home_bot is not a Git repository."
fi

# Get current date in "yyyy-mm-dd" format
fecha_actual=$(date +%Y-%m-%d)

# Temporary file path
archivo_tmp="$tmp_dir/$fecha_actual-post.md"

# Destination directory
directorio_destino="$home_bot$posts_dir"

# Check if the temporary file exists
if [[ -f "$archivo_tmp" ]]; then
    log "Temporary file found: $archivo_tmp"

    # Save the current branch to return to later
    current_branch=$(git rev-parse --abbrev-ref HEAD)
    log "Current branch: $current_branch"

    # Store the original branch to return to
    original_branch="$current_branch"

    # Switch to gh-pages branch
    log "Switching to gh-pages branch..."
    git_safe checkout gh-pages

    # Move the file to destination
    log "Moving $archivo_tmp to $directorio_destino..."
    if ! mv "$archivo_tmp" "$directorio_destino"; then
        # If move fails, switch back to original branch before exiting
        git_safe checkout "$original_branch" || log "Warning: Could not return to original branch"
        error_exit "Could not move file."
    fi
    log "File moved successfully."

    # Pull latest changes to avoid conflicts
    log "Pulling latest changes from remote gh-pages..."
    git_safe pull origin gh-pages || log "Warning: Pull failed, continuing anyway..."

    # Add changes to Git
    log "Adding changes to Git..."
    git_safe add "$directorio_destino"

    # Check if there are actually changes to commit
    if git diff-index --quiet HEAD --; then
        log "No changes to commit."
    else
        # Perform commit
        log "Committing changes..."
        git_safe commit -m "Post: $fecha_actual"

        # Push changes
        log "Pushing changes..."
        git_safe push origin gh-pages
    fi

    # Return to the original branch
    log "Returning to original branch ($original_branch)..."
    git_safe checkout "$original_branch"

    log "Publication process completed for $fecha_actual."
else
    log "No file found at $archivo_tmp. Nothing to publish."
fi

log "postBotElectrico.sh finished."