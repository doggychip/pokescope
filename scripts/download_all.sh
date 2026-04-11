#!/bin/bash
# Download all cards from PokémonTCG API in batches
set -e

DIR="$(cd "$(dirname "$0")" && pwd)/seed_data"
mkdir -p "$DIR"

PAGE_SIZE=250
TOTAL=20237
PAGES=$(( (TOTAL + PAGE_SIZE - 1) / PAGE_SIZE ))

echo "Downloading $TOTAL cards across $PAGES pages..."

for page in $(seq 1 $PAGES); do
  OUT="$DIR/page_${page}.json"
  if [ -f "$OUT" ] && [ -s "$OUT" ]; then
    echo "  Page $page already downloaded, skipping"
    continue
  fi

  for attempt in 1 2 3 4 5; do
    echo "  Fetching page $page (attempt $attempt)..."
    if curl -s --max-time 60 "https://api.pokemontcg.io/v2/cards?page=${page}&pageSize=${PAGE_SIZE}" -o "$OUT" 2>/dev/null; then
      # Verify it's valid JSON with data
      COUNT=$(python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(len(d.get('data',[])))" "$OUT" 2>/dev/null || echo "0")
      if [ "$COUNT" -gt 0 ]; then
        echo "    Got $COUNT cards"
        break
      fi
    fi
    echo "    Failed, retrying..."
    rm -f "$OUT"
    sleep $((attempt * 2))
  done

  # Rate limit courtesy
  sleep 0.5
done

echo "Done! Counting total cards..."
python3 -c "
import json, glob, os
total = 0
for f in sorted(glob.glob(os.path.join('$DIR', 'page_*.json'))):
    d = json.load(open(f))
    total += len(d.get('data', []))
print(f'Total cards downloaded: {total}')
"
