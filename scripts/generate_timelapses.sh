#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="${BASE_DIR:-$HOME/Documents/Screenshots}"
FPS=30
OVERWRITE=false
DELETE=false
PYTHON="${PYTHON:-python3}"

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Loops through all date directories under BASE_DIR (YYYY/MM/DD) and
invokes timelapse.py to create MP4 timelapse videos.

Options:
  --base-dir PATH       Base screenshots directory (default: $BASE_DIR)
  --fps N               Frames per second (default: $FPS)
  --overwrite           Overwrite existing output videos
  --delete              Delete screenshots after generation or when video already exists
  --python PATH         Python interpreter to run timelapse.py (default: $PYTHON)
  -h, --help            Show this help

Examples:
  $(basename "$0") --base-dir "$HOME/Documents/Screenshots" --fps 24
  $(basename "$0") --overwrite --delete
  $(basename "$0") --missing-only
EOF
}

# Parse long options
while [[ $# -gt 0 ]]; do
  case "$1" in
    --base-dir)
      BASE_DIR="$2"; shift 2;;
    --fps)
      FPS="$2"; shift 2;;
    --overwrite)
      OVERWRITE=true; shift;;
    --delete)
      DELETE=true; shift;;
    --python)
      PYTHON="$2"; shift 2;;
    -h|--help)
      usage; exit 0;;
    *)
      echo "Unknown option: $1" >&2
      usage; exit 1;;
  esac
done

# Resolve timelapse.py path (repo root is one level up from scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TL_SCRIPT="$REPO_DIR/timelapse.py"

if [[ ! -f "$TL_SCRIPT" ]]; then
  echo "timelapse.py not found at $TL_SCRIPT" >&2
  exit 1
fi

# Iterate through YYYY/MM/DD directories
found_any=false
for year_dir in "$BASE_DIR"/*; do
  [[ -d "$year_dir" ]] || continue
  year_base="$(basename "$year_dir")"
  [[ "$year_base" =~ ^[0-9]{4}$ ]] || continue
  for month_dir in "$year_dir"/*; do
    [[ -d "$month_dir" ]] || continue
    month_base="$(basename "$month_dir")"
    [[ "$month_base" =~ ^[0-9]{2}$ ]] || continue
    for day_dir in "$month_dir"/*; do
      [[ -d "$day_dir" ]] || continue
      day_base="$(basename "$day_dir")"
      [[ "$day_base" =~ ^[0-9]{2}$ ]] || continue

      found_any=true

      date_str="$year_base-$month_base-$day_base"

      # Skip today's date as it is still ongoing
      TODAY="$(date +%Y-%m-%d)"
      if [[ "$date_str" == "$TODAY" ]]; then
        echo "$date_str - skipped: today; ongoing"
        continue
      fi

      cmd=("$PYTHON" "$TL_SCRIPT" --date "$date_str" --base-dir "$BASE_DIR" --fps "$FPS" --skip-if-existing)
      [[ "$OVERWRITE" == true ]] && cmd+=("--overwrite")
      [[ "$DELETE" == true ]] && cmd+=("--delete")

      "${cmd[@]}"
    done
  done
done

if [[ "$found_any" != true ]]; then
  echo "No date directories found under $BASE_DIR"
else
  echo "All done."
fi
