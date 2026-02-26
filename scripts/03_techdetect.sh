#!/usr/bin/env bash
set -euo pipefail

# Phase 3: Technology detection and screenshots
# Usage:
#   scripts/03_techdetect.sh <outdir>
# Example:
#   scripts/03_techdetect.sh runs/<id>

OUTDIR="${1:-output}"

# Ensure relative helper paths work regardless of where you run this from
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

# Tuning knobs
SCREENSHOT_THREADS="${SCREENSHOT_THREADS:-10}"
WAPPALYZER_THREADS="${WAPPALYZER_THREADS:-25}"

mkdir -p "$OUTDIR/screenshots" "$OUTDIR/tmp"

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing: $1 (skipping $2)"; return 1; }; }

if [[ ! -f "$OUTDIR/final.urls.txt" ]]; then
  echo "[!] No final.urls.txt found. Run subdomain enumeration first."
  exit 1
fi

# Technology detection with httpx (already has some built-in tech detection)
echo "[+] Enhanced technology detection"
if need httpx "httpx tech detection"; then
  echo "    Running httpx with technology detection flags"
  
  HTTP_BASE=( -silent -j -t 50 )
  
  httpx -l "$OUTDIR/final.urls.txt" "${HTTP_BASE[@]}" \
    -favicon \
    -tech-detect \
    -status-code \
    -content-length \
    -content-type \
    -web-server \
    -response-time \
    -cdn \
    -o "$OUTDIR/httpx.tech.jsonl" || true
  
  echo "    Tech detection complete: httpx.tech.jsonl"
fi

# Technology detection with Wappalyzer (if available)
if need wappy "wappalyzer"; then
  echo "[+] Running Wappalyzer technology detection"
  
  wappy -l "$OUTDIR/final.urls.txt" \
    -t "$WAPPALYZER_THREADS" \
    -o "$OUTDIR/wappalyzer.json" || true
  
  echo "    Wappalyzer results: wappalyzer.json"
fi

# Wayback URLs (using waybackurls or gau)
if need waybackurls "wayback URL collection"; then
  echo "[+] Collecting wayback URLs"
  
  cat "$OUTDIR/hosts.resolved.txt" 2>/dev/null \
    | waybackurls \
    | tee "$OUTDIR/wayback.urls.txt" \
    | grep -E '\.(js|json|xml|conf|config|bak|backup|sql|log)$' \
    > "$OUTDIR/wayback.interesting.txt" || true
  
  echo "    Wayback URLs: $(wc -l < "$OUTDIR/wayback.urls.txt" 2>/dev/null || echo 0)"
  echo "    Interesting files: $(wc -l < "$OUTDIR/wayback.interesting.txt" 2>/dev/null || echo 0)"
elif need gau "gau URL collection"; then
  echo "[+] Collecting URLs with gau"
  
  cat "$OUTDIR/hosts.resolved.txt" 2>/dev/null \
    | gau --threads 5 \
    | tee "$OUTDIR/wayback.urls.txt" \
    | grep -E '\.(js|json|xml|conf|config|bak|backup|sql|log)$' \
    > "$OUTDIR/wayback.interesting.txt" || true
  
  echo "    GAU URLs: $(wc -l < "$OUTDIR/wayback.urls.txt" 2>/dev/null || echo 0)"
  echo "    Interesting files: $(wc -l < "$OUTDIR/wayback.interesting.txt" 2>/dev/null || echo 0)"
fi

# JavaScript file extraction
if [[ -f "$OUTDIR/httpx.jsonl" ]]; then
  echo "[+] Extracting JavaScript files from httpx responses"
  
  jq -r '.url' "$OUTDIR/httpx.jsonl" 2>/dev/null \
    | grep -iE '\.js(\?|$)' \
    | sort -u > "$OUTDIR/js.files.txt" || true
  
  echo "    JavaScript files: $(wc -l < "$OUTDIR/js.files.txt" 2>/dev/null || echo 0)"
fi

# Screenshot capture (if gowitness or aquatone available)
if [[ "${ENABLE_SCREENSHOTS:-false}" == "true" ]]; then
  if need gowitness "screenshot capture"; then
    echo "[+] Capturing screenshots with gowitness"
    
    gowitness file -f "$OUTDIR/final.urls.txt" \
      --threads "$SCREENSHOT_THREADS" \
      --screenshot-path "$OUTDIR/screenshots" \
      --db-path "$OUTDIR/gowitness.db" \
      --timeout 15 || true
    
    echo "    Screenshots saved to: $OUTDIR/screenshots/"
  elif need aquatone "screenshot capture"; then
    echo "[+] Capturing screenshots with aquatone"
    
    cat "$OUTDIR/final.urls.txt" \
      | aquatone \
        -threads "$SCREENSHOT_THREADS" \
        -out "$OUTDIR/aquatone" || true
    
    echo "    Aquatone report: $OUTDIR/aquatone/aquatone_report.html"
  fi
fi

# Extract parameters from URLs
if need unfurl "URL parameter extraction"; then
  echo "[+] Extracting URL parameters"
  
  if [[ -f "$OUTDIR/wayback.urls.txt" ]]; then
    cat "$OUTDIR/wayback.urls.txt" \
      | unfurl --unique keys \
      | sort -u > "$OUTDIR/params.txt" || true
    
    echo "    Unique parameters: $(wc -l < "$OUTDIR/params.txt" 2>/dev/null || echo 0)"
  fi
fi

echo "[+] Technology detection complete."
