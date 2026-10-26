#!/bin/bash
# Wrapper script for fast security scan
# Filters out empty arguments that poe may insert

set -e

# Filter out empty strings from arguments
args=()
for arg in "$@"; do
    if [ -n "$arg" ]; then
        args+=("$arg")
    fi
done

# Execute the scanner with fast-scan preset
exec python -m src.scanner.main automation --config-file resources/config/fast-scan.json "${args[@]}"
