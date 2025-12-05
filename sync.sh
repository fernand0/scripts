#!/bin/sh

set -e

REMOTE_HOST="ftricass@ra-amon.cps.unizar.es"

#echo "Checking connection to ${REMOTE_HOST}..."
#ssh -o BatchMode=yes -o ConnectTimeout=10 ${REMOTE_HOST} exit
#echo "Connection successful."

if [ -z "$SSH_AUTH_SOCK" ]; then
    eval "$(ssh-agent -s)"
fi

if ! ssh-add -l | grep -q "$(ssh-keygen -lf ~/.ssh/id_rsa | awk '{print $2}')"; then
    ssh-add ~/.ssh/id_rsa
fi

echo "Deleting local empty directories..."
find . -type d -empty -delete || true

echo "Syncing with remote (pre-move)..."
rsync -avz --delete . ${REMOTE_HOST}:Music/sync/

echo "Moving remote directories..."
ssh ${REMOTE_HOST} '
    set -e
    DIR_TO_MOVE=$(find ~/Music/podcasts/ -mindepth 1 -maxdepth 1 -type d | sort | head -n 1)
    if [ -n "${DIR_TO_MOVE}" ]; then
        echo "Moving directory ${DIR_TO_MOVE} in remote"
        mv "${DIR_TO_MOVE}" ~/Music/sync/
    else
        echo "No directories to move in remote"
    fi
'
echo "Remote directories moved."

echo "Syncing with remote (post-move)..."
rsync -avz ${REMOTE_HOST}:Music/sync/ .
echo "Sync finished."

