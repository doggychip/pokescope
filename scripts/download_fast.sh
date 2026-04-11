#!/bin/bash
# Fast parallel download of all card pages
set -e

DIR="$(cd "$(dirname "$0")" && pwd)/seed_data"
mkdir -p "$DIR"

PAGE_SIZE=250
TOTAL=20237
PAGES=$(( (TOTAL + PAGE_SIZE - 1) / PAGE_SIZE ))

download_page() {
  local page=$1
  local out="$DIR/page_${page}.json"

  if [ -f "$out" ] && [ -s "$out" ]; then
    local count=$(python3 -c "import json; d=json.load(open('$out')); print(len(d.get('data',[])))" 2>/dev/null || echo "0")
    if [ "$count" -gt "0" ]; then
      return 0
    fi
  fi

  for attempt in 1 2 3 4 5 6 7 8; do
    if curl -s --max-time 45 --retry 2 "https://api.pokemontcg.io/v2/cards?page=${page}&pageSize=${PAGE_SIZE}" -o "$out" 2>/dev/null; then
      local count=$(python3 -c "import json; d=json.load(open('$out')); print(len(d.get('data',[])))" 2>/dev/null || echo "0")
      if [ "$count" -gt "0" ]; then
        echo "  Page $page: $count cards"
        return 0
      fi
    fi
    rm -f "$out"
    sleep $((attempt))
  done
  echo "  Page $page: FAILED after 8 attempts"
  return 1
}

echo "Downloading $TOTAL cards across $PAGES pages (parallel)..."

# Run 3 at a time to avoid rate limiting
for batch_start in $(seq 1 3 $PAGES); do
  pids=()
  for offset in 0 1 2; do
    page=$((batch_start + offset))
    if [ "$page" -le "$PAGES" ]; then
      download_page "$page" &
      pids+=($!)
    fi
  done
  for pid in "${pids[@]}"; do
    wait "$pid" 2>/dev/null || true
  done
  sleep 1
done

echo ""
echo "Download complete. Counting..."
python3 -c "
import json, glob, os
total = 0
files = sorted(glob.glob(os.path.join('$DIR', 'page_*.json')))
for f in files:
    try:
        d = json.load(open(f))
        total += len(d.get('data', []))
    except: pass
print(f'Files: {len(files)}/{$PAGES}')
print(f'Total cards: {total}')
"
