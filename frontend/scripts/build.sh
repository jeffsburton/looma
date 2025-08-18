#!/usr/bin/env bash
# Build script for Vite/Vue frontend
# Usage:
#   ./scripts/build.sh                              # build with default targets
#   BUILD_TARGET=es2020 ./scripts/build.sh          # override JS build target via env
#   ./scripts/build.sh --install                    # install deps then build
#   ./scripts/build.sh -p http://localhost:8000     # set proxy target (LOOMA_API_URL)
#   ./scripts/build.sh http://localhost:9000        # positional proxy target

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

INSTALL=0
PROXY_TARGET=""
DEFAULT_PROXY="http://127.0.0.1:8000"

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    -i|--install)
      INSTALL=1
      shift
      ;;
    -p|--proxy)
      PROXY_TARGET="${2:-}"
      if [[ -z "$PROXY_TARGET" ]]; then
        echo "Error: --proxy requires a value" >&2
        exit 1
      fi
      shift 2
      ;;
    -h|--help)
      sed -n '2,20p' "$0"
      exit 0
      ;;
    *)
      # treat as positional proxy target
      PROXY_TARGET="$1"
      shift
      ;;
  esac
done

cd "$FRONTEND_DIR"

if [[ $INSTALL -eq 1 ]]; then
  echo "Installing dependencies with npm ci..."
  npm ci
fi

if [[ -n "${BUILD_TARGET:-}" ]]; then
  echo "Building with BUILD_TARGET=$BUILD_TARGET (from environment)"
else
  echo "Building with default target (vite.config.js default)"
fi

# Determine proxy target to export for the build step (for parity/workflows)
if [[ -z "$PROXY_TARGET" ]]; then
  PROXY_TARGET="$DEFAULT_PROXY"
fi

echo "Using proxy target (LOOMA_API_URL): $PROXY_TARGET"
LOOMA_API_URL="$PROXY_TARGET" npm run build

if [[ -d "dist" ]]; then
  echo "Build complete. Output: $FRONTEND_DIR/dist"
else
  echo "Build failed: dist directory not found." >&2
  exit 1
fi
