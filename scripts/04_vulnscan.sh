#!/usr/bin/env bash
set -euo pipefail

# Phase 4: Vulnerability scanning with nuclei
# Usage:
#   scripts/04_vulnscan.sh <outdir>
# Example:
#   scripts/04_vulnscan.sh runs/<id>

OUTDIR="${1:-output}"

# Ensure relative helper paths work regardless of where you run this from
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

# Tuning knobs
NUCLEI_THREADS="${NUCLEI_THREADS:-50}"
NUCLEI_RATE="${NUCLEI_RATE:-150}"
NUCLEI_SEVERITY="${NUCLEI_SEVERITY:-critical,high,medium}"
NUCLEI_TEMPLATES="${NUCLEI_TEMPLATES:-}"  # empty = all templates

mkdir -p "$OUTDIR/vulns" "$OUTDIR/tmp"

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing: $1 (skipping $2)"; return 1; }; }

if [[ ! -f "$OUTDIR/final.urls.txt" ]]; then
  echo "[!] No final.urls.txt found. Run subdomain enumeration first."
  exit 1
fi

# Update nuclei templates
if need nuclei "nuclei scanning"; then
  echo "[+] Updating nuclei templates"
  nuclei -update-templates -silent || true
  
  echo "[+] Running nuclei vulnerability scan"
  echo "    Severity: $NUCLEI_SEVERITY"
  echo "    Threads: $NUCLEI_THREADS"
  
  NUCLEI_ARGS=(
    -list "$OUTDIR/final.urls.txt"
    -silent
    -json
    -o "$OUTDIR/vulns/nuclei.jsonl"
    -severity "$NUCLEI_SEVERITY"
    -c "$NUCLEI_THREADS"
    -rl "$NUCLEI_RATE"
    -stats
    -stats-interval 30
  )
  
  if [[ -n "$NUCLEI_TEMPLATES" ]]; then
    NUCLEI_ARGS+=( -t "$NUCLEI_TEMPLATES" )
  fi
  
  nuclei "${NUCLEI_ARGS[@]}" || true
  
  # Create human-readable report
  if [[ -f "$OUTDIR/vulns/nuclei.jsonl" ]]; then
    echo "[+] Creating summary report"
    
    jq -r '[.info.severity, .info.name, .host, .matched_at] | @tsv' \
      "$OUTDIR/vulns/nuclei.jsonl" 2>/dev/null \
      | sort -k1,1 -k2,2 \
      > "$OUTDIR/vulns/nuclei.summary.tsv" || true
    
    # Count by severity
    {
      echo "=== Nuclei Vulnerability Summary ==="
      echo ""
      echo "By Severity:"
      jq -r '.info.severity' "$OUTDIR/vulns/nuclei.jsonl" 2>/dev/null | sort | uniq -c | sort -rn || true
      echo ""
      echo "Total findings: $(wc -l < "$OUTDIR/vulns/nuclei.jsonl" 2>/dev/null || echo 0)"
      echo ""
      echo "By Template:"
      jq -r '.info.name' "$OUTDIR/vulns/nuclei.jsonl" 2>/dev/null | sort | uniq -c | sort -rn | head -20 || true
    } > "$OUTDIR/vulns/nuclei.stats.txt"
    
    echo "    Results: $OUTDIR/vulns/nuclei.jsonl"
    echo "    Summary: $OUTDIR/vulns/nuclei.summary.tsv"
    cat "$OUTDIR/vulns/nuclei.stats.txt"
  fi
fi

# Additional security checks with nikto (if enabled and available)
if [[ "${ENABLE_NIKTO:-false}" == "true" ]] && need nikto "nikto scanning"; then
  echo "[+] Running nikto web server scanner (this may take a long time)"
  
  mkdir -p "$OUTDIR/vulns/nikto"
  
  while IFS= read -r url; do
    host=$(echo "$url" | sed -E 's|https?://||' | cut -d/ -f1)
    safe_name=$(echo "$host" | tr ':/' '_')
    
    nikto -h "$url" \
      -output "$OUTDIR/vulns/nikto/${safe_name}.txt" \
      -Format txt \
      -Tuning 123456789 \
      -maxtime 300 || true
  done < "$OUTDIR/final.urls.txt"
  
  echo "    Nikto results: $OUTDIR/vulns/nikto/"
fi

# Check for common security headers
echo "[+] Analyzing security headers"
if [[ -f "$OUTDIR/httpx.jsonl" ]]; then
  python3 "$ROOT_DIR/helpers/analyze_headers.py" \
    --httpx "$OUTDIR/httpx.jsonl" \
    --output "$OUTDIR/vulns/security_headers.tsv" || true
  
  echo "    Security headers analysis: $OUTDIR/vulns/security_headers.tsv"
fi

# Check for subdomain takeover potential
if need subzy "subdomain takeover check"; then
  echo "[+] Checking for subdomain takeover vulnerabilities"
  
  subzy run \
    --targets "$OUTDIR/hosts.resolved.txt" \
    --output "$OUTDIR/vulns/subdomain_takeover.json" \
    --json || true
  
  echo "    Takeover check: $OUTDIR/vulns/subdomain_takeover.json"
elif need subjack "subdomain takeover check"; then
  echo "[+] Checking for subdomain takeover with subjack"
  
  subjack -w "$OUTDIR/hosts.resolved.txt" \
    -t 20 \
    -ssl \
    -o "$OUTDIR/vulns/subdomain_takeover.txt" || true
  
  echo "    Takeover check: $OUTDIR/vulns/subdomain_takeover.txt"
fi

echo "[+] Vulnerability scanning complete."
