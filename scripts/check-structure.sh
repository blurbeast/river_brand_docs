#!/usr/bin/env bash
# Riverbrand Knowledge Book — structure checker entry point.
# Usage: scripts/check-structure.sh [--toc] [--no-wordcount]
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$DIR/check_structure.py" "$@"
