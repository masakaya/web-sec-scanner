#!/bin/bash
# Wrapper script for thorough security scan
# Filters out empty arguments that poe may insert

set -e

# Filter out empty strings from arguments
args=()
for arg in "$@"; do
    if [ -n "$arg" ]; then
        args+=("$arg")
    fi
done

# Execute the scanner with thorough-scan preset
exec python -m src.scanner.main automation --config-file resources/config/thorough-scan.json "${args[@]}"
