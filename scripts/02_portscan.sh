#!/usr/bin/env bash
set -euo pipefail

# Phase 2: Port scanning and service detection
# Usage:
#   scripts/02_portscan.sh <outdir>
# Example:
#   scripts/02_portscan.sh runs/<id>

OUTDIR="${1:-output}"

# Ensure relative helper paths work regardless of where you run this from
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

# Tuning knobs (override via env / .env loaded by bin/recon)
NMAP_THREADS="${NMAP_THREADS:-50}"
NMAP_PORTS="${NMAP_PORTS:-top-ports 1000}"  # or "p 1-65535" for full scan
NMAP_RATE="${NMAP_RATE:-1000}"  # packets per second
NAABU_RATE="${NAABU_RATE:-1000}"
NAABU_PORTS="${NAABU_PORTS:-top-ports full}"  # "full" or "p 1-65535"

mkdir -p "$OUTDIR/tmp"

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing: $1 (skipping $2)"; return 1; }; }

if [[ ! -f "$OUTDIR/hosts.resolved.txt" ]]; then
  echo "[!] No hosts.resolved.txt found. Run subdomain enumeration first."
  exit 1
fi

# Extract IPs from DNS data for direct scanning
if [[ -f "$OUTDIR/dns.A.jsonl" ]]; then
  echo "[+] Extracting unique IP addresses from DNS results"
  jq -r '.a[]? // empty' "$OUTDIR/dns.A.jsonl" 2>/dev/null | sort -u > "$OUTDIR/ips.txt" || true
  jq -r '.aaaa[]? // empty' "$OUTDIR/dns.AAAA.jsonl" 2>/dev/null | sort -u >> "$OUTDIR/ips.txt" || true
  sort -u "$OUTDIR/ips.txt" -o "$OUTDIR/ips.txt"
  echo "    unique IPs: $(wc -l < "$OUTDIR/ips.txt")"
fi

# Fast port scan with naabu (if available)
if need naabu "naabu port scan"; then
  echo "[+] Running fast port scan with naabu"
  
  if [[ -f "$OUTDIR/ips.txt" ]]; then
    naabu -silent -list "$OUTDIR/ips.txt" \
      -rate "$NAABU_RATE" \
      -"$NAABU_PORTS" \
      -json \
      -o "$OUTDIR/ports.naabu.jsonl" || true
  fi
  
  # Also scan resolved hostnames
  if [[ -f "$OUTDIR/hosts.resolved.txt" ]]; then
    naabu -silent -list "$OUTDIR/hosts.resolved.txt" \
      -rate "$NAABU_RATE" \
      -"$NAABU_PORTS" \
      -json \
      -o "$OUTDIR/ports.hosts.naabu.jsonl" || true
  fi
  
  # Merge and create simple host:port list
  cat "$OUTDIR/ports.naabu.jsonl" "$OUTDIR/ports.hosts.naabu.jsonl" 2>/dev/null \
    | jq -r '"\(.host):\(.port)"' \
    | sort -u > "$OUTDIR/open.ports.txt" || true
  
  echo "    open ports found: $(wc -l < "$OUTDIR/open.ports.txt" 2>/dev/null || echo 0)"
fi

# Service detection with nmap (if available and requested)
if [[ "${ENABLE_NMAP:-false}" == "true" ]] && need nmap "nmap service detection"; then
  echo "[+] Running nmap service detection (this may take a while)"
  
  if [[ -f "$OUTDIR/ips.txt" ]] && [[ -s "$OUTDIR/ips.txt" ]]; then
    # Run nmap with service version detection
    nmap -iL "$OUTDIR/ips.txt" \
      -"$NMAP_PORTS" \
      -sV -sC \
      --min-rate "$NMAP_RATE" \
      --max-retries 2 \
      -T4 \
      -oX "$OUTDIR/nmap.xml" \
      -oN "$OUTDIR/nmap.txt" || true
    
    echo "    nmap results saved to nmap.xml and nmap.txt"
  fi
fi

echo "[+] Port scan complete."
if [[ -f "$OUTDIR/open.ports.txt" ]]; then
  echo "    Results: $OUTDIR/open.ports.txt"
fi
