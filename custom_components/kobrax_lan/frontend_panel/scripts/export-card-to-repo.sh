#!/usr/bin/env bash
set -euo pipefail

CARD_REPO_PATH="${CARD_REPO_PATH:-../../../../kobrax-lan-hass-card}"
SOURCE="$(cd "$(dirname "$0")/.." && pwd)/dist/kobrax-lan-card.js"
TARGET_DIR="$(cd "$CARD_REPO_PATH" && pwd)"
TARGET="$TARGET_DIR/kobrax-lan-card.js"

if [[ ! -f "$SOURCE" ]]; then
  echo "Build artifact not found: $SOURCE" >&2
  exit 1
fi

cp "$SOURCE" "$TARGET"
echo "Exported card artifact to $TARGET"
