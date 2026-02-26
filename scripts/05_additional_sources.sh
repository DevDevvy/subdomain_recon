#!/usr/bin/env bash
set -euo pipefail

# Additional subdomain enumeration sources
# Usage:
#   scripts/05_additional_sources.sh <domains_file> <outdir>

DOMAINS_FILE="${1:-input/domains.txt}"
OUTDIR="${2:-output}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

mkdir -p "$OUTDIR/tmp"

need() { command -v "$1" >/dev/null 2>&1 || { echo "   [!] $1 not installed (skipping)"; return 1; }; }

echo "[+] Running additional subdomain enumeration sources"

# Amass (passive mode)
if need amass; then
  echo "   [+] Running amass (passive)"
  amass enum -passive -d "$DOMAINS_FILE" -o "$OUTDIR/tmp/subs.amass.txt" || true
  sort -u "$OUTDIR/tmp/subs.amass.txt" -o "$OUTDIR/tmp/subs.amass.txt" 2>/dev/null || true
  echo "      Found: $(wc -l < "$OUTDIR/tmp/subs.amass.txt" 2>/dev/null || echo 0)"
fi

# Assetfinder
if need assetfinder; then
  echo "   [+] Running assetfinder"
  cat "$DOMAINS_FILE" | assetfinder --subs-only > "$OUTDIR/tmp/subs.assetfinder.txt" || true
  sort -u "$OUTDIR/tmp/subs.assetfinder.txt" -o "$OUTDIR/tmp/subs.assetfinder.txt" 2>/dev/null || true
  echo "      Found: $(wc -l < "$OUTDIR/tmp/subs.assetfinder.txt" 2>/dev/null || echo 0)"
fi

# Findomain
if need findomain; then
  echo "   [+] Running findomain"
  findomain -f "$DOMAINS_FILE" -q -u "$OUTDIR/tmp/subs.findomain.txt" || true
  sort -u "$OUTDIR/tmp/subs.findomain.txt" -o "$OUTDIR/tmp/subs.findomain.txt" 2>/dev/null || true
  echo "      Found: $(wc -l < "$OUTDIR/tmp/subs.findomain.txt" 2>/dev/null || echo 0)"
fi

# crt.sh
if need curl; then
  echo "   [+] Querying crt.sh"
  > "$OUTDIR/tmp/subs.crtsh.txt"
  while IFS= read -r domain; do
    curl -s "https://crt.sh/?q=%.${domain}&output=json" 2>/dev/null \
      | jq -r '.[].name_value' 2>/dev/null \
      | sed 's/^\*\.//g' \
      | sed 's/\.$//g' \
      | tr '[:upper:]' '[:lower:]' \
      >> "$OUTDIR/tmp/subs.crtsh.txt" || true
  done < "$DOMAINS_FILE"
  sort -u "$OUTDIR/tmp/subs.crtsh.txt" -o "$OUTDIR/tmp/subs.crtsh.txt" 2>/dev/null || true
  echo "      Found: $(wc -l < "$OUTDIR/tmp/subs.crtsh.txt" 2>/dev/null || echo 0)"
fi

# GitHub subdomain enumeration (github-subdomains)
if need github-subdomains; then
  echo "   [+] Running github-subdomains"
  cat "$DOMAINS_FILE" | github-subdomains -t "$GITHUB_TOKEN" > "$OUTDIR/tmp/subs.github.txt" 2>/dev/null || true
  sort -u "$OUTDIR/tmp/subs.github.txt" -o "$OUTDIR/tmp/subs.github.txt" 2>/dev/null || true
  echo "      Found: $(wc -l < "$OUTDIR/tmp/subs.github.txt" 2>/dev/null || echo 0)"
fi

# Merge all sources
echo "[+] Merging all subdomain sources"
cat "$OUTDIR/subs.txt" \
    "$OUTDIR/tmp/subs.amass.txt" \
    "$OUTDIR/tmp/subs.assetfinder.txt" \
    "$OUTDIR/tmp/subs.findomain.txt" \
    "$OUTDIR/tmp/subs.crtsh.txt" \
    "$OUTDIR/tmp/subs.github.txt" 2>/dev/null \
  | sed 's/^\*\.//g' \
  | sed 's/\.$//g' \
  | tr '[:upper:]' '[:lower:]' \
  | awk 'NF' \
  | sort -u > "$OUTDIR/subs.all.txt"

# Count new discoveries
OLD_COUNT=$(wc -l < "$OUTDIR/subs.txt")
NEW_COUNT=$(wc -l < "$OUTDIR/subs.all.txt")
ADDED=$((NEW_COUNT - OLD_COUNT))

echo "   Previous: $OLD_COUNT subdomains"
echo "   Now:      $NEW_COUNT subdomains"
echo "   Added:    $ADDED new subdomains"

# Backup original and replace
cp "$OUTDIR/subs.txt" "$OUTDIR/subs.original.txt"
mv "$OUTDIR/subs.all.txt" "$OUTDIR/subs.txt"

echo "[+] Enhanced subdomain list saved to subs.txt"
echo "    Original saved as subs.original.txt"
