#!/usr/bin/env bash
# Start Vite dev server with configurable API proxy target
# Usage:
#   ./scripts/dev.sh                     # uses default http://127.0.0.1:8000
#   ./scripts/dev.sh http://localhost:9000
#   ./scripts/dev.sh -t https://api.example.com
#   ./scripts/dev.sh --install -t http://localhost:8000

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

INSTALL=0
TARGET=""
DEFAULT_TARGET="http://127.0.0.1:8000"

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    -i|--install)
      INSTALL=1
      shift
      ;;
    -t|--target)
      TARGET="${2:-}"
      if [[ -z "$TARGET" ]]; then
        echo "Error: --target requires a value" >&2
        exit 1
      fi
      shift 2
      ;;
    -h|--help)
      sed -n '2,20p' "$0"
      exit 0
      ;;
    *)
      # positional: proxy target value
      TARGET="$1"
      shift
      ;;
  esac
done

cd "$FRONTEND_DIR"

if [[ $INSTALL -eq 1 ]]; then
  echo "Installing dependencies with npm ci..."
  npm ci
fi

if [[ -z "$TARGET" ]]; then
  TARGET="$DEFAULT_TARGET"
fi

echo "Starting Vite with proxy target: $TARGET"
# Use LOOMA_API_URL which vite.config.js prefers for proxy target.
LOOMA_API_URL="$TARGET" npm run dev
