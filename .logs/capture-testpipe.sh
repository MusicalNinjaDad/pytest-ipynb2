#!/bin/bash
WATCH_DIR="/tmp"
DEST_DIR="$WORKSPACE_DIR/.logs"
mkdir -p "$DEST_DIR"

inotifywait -m -e create "$WATCH_DIR" --format '%w%f' | \
while read filepath; do
    if [[ $(basename "$filepath") == test-ids-*.txt ]]; then
        # Give the file a brief moment to be written fully
        sleep 0.1
        cp "$filepath" "$DEST_DIR/"
        echo "Captured $(basename "$filepath")"
    fi
done
