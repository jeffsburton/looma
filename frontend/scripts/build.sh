#!/usr/bin/env bash
# Build script for Vite/Vue frontend
# Usage examples:
#   ./scripts/build.sh                    # build with default target from vite.config.js
#   ./scripts/build.sh es2020             # build with target=es2020
#   ./scripts/build.sh -t es2020          # same as above
#   ./scripts/build.sh --install -t es2020 # install deps then build

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

INSTALL=0
TARGET=""

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
      # positional: target value
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

if [[ -n "$TARGET" ]]; then
  echo "Building with Vite build.target=$TARGET"
  BUILD_TARGET="$TARGET" npm run build
else
  echo "Building with default target (vite.config.js)"
  npm run build
fi

if [[ -d "dist" ]]; then
  echo "Build complete. Output: $FRONTEND_DIR/dist"
else
  echo "Build failed: dist directory not found." >&2
  exit 1
fi
