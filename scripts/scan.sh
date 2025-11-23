#!/bin/bash
# Wrapper script for security scanner
# Filters out empty arguments that poe may insert

set -e

# Filter out empty strings from arguments
args=()
for arg in "$@"; do
    if [ -n "$arg" ]; then
        args+=("$arg")
    fi
done

# Execute the scanner
exec python -m src.scanner.main "${args[@]}"
