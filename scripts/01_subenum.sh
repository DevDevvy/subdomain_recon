#!/usr/bin/env bash
set -euo pipefail

# Phase 1: subdomain enumeration + validation + wildcard-aware classification
# Usage:
#   scripts/01_subenum.sh <domains_file> <outdir>
# Example:
#   scripts/01_subenum.sh runs/<id>/domains.txt runs/<id>

DOMAINS_FILE="${1:-input/domains.txt}"
OUTDIR="${2:-output}"

# Ensure relative helper paths work regardless of where you run this from
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

# Tuning knobs (override via env / .env loaded by bin/recon)
SUBFINDER_FLAGS="${SUBFINDER_FLAGS:--silent -all -recursive}"

DNS_THREADS="${DNS_THREADS:-200}"
DNS_RETRY="${DNS_RETRY:-2}"
DNS_RL="${DNS_RL:-300}"              # DNS queries/sec (set 0 to disable)
WILDCARD_SAMPLES="${WILDCARD_SAMPLES:-4}"  # random hosts per root
RESOLVERS_FILE="${RESOLVERS_FILE:-}"       # optional: path to resolvers.txt

HTTP_THREADS="${HTTP_THREADS:-75}"
HTTP_RL="${HTTP_RL:-150}"            # HTTP requests/sec (set 0 to disable)
HTTP_TIMEOUT="${HTTP_TIMEOUT:-10}"
HTTP_FOLLOW_REDIRECTS="${HTTP_FOLLOW_REDIRECTS:-true}" # true/false

mkdir -p "$OUTDIR/tmp"

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing: $1"; exit 1; }; }
need subfinder
need dnsx
need httpx
need python3
need jq

echo "[+] 0) Inputs"
echo "    domains: $DOMAINS_FILE"
echo "    outdir:  $OUTDIR"

# ---- 1) Subdomain enumeration ----
echo "[+] 1) Subdomain enumeration (subfinder)"
subfinder -dL "$DOMAINS_FILE" $SUBFINDER_FLAGS -o "$OUTDIR/subs.raw.txt"

echo "[+] Normalize + dedupe (strip wildcard prefixes, trailing dots, lowercase)"
cat "$OUTDIR/subs.raw.txt" \
  | sed 's/^\*\.\(.*\)$/\1/' \
  | sed 's/\.$//' \
  | tr '[:upper:]' '[:lower:]' \
  | awk 'NF' \
  | sort -u > "$OUTDIR/subs.txt"

# Ensure apex domains are included (subfinder may not always emit them)
cat "$DOMAINS_FILE" \
  | sed 's/#.*//' \
  | tr '[:upper:]' '[:lower:]' \
  | sed 's/\.$//' \
  | awk 'NF' >> "$OUTDIR/subs.txt"
sort -u "$OUTDIR/subs.txt" -o "$OUTDIR/subs.txt"

echo "    subs: $(wc -l < "$OUTDIR/subs.txt")"

# ---- 2) DNS resolve ----
echo "[+] 2) DNS resolve (A + AAAA) JSONL (omit raw)"
DNS_BASE=( -silent -json -omit-raw -t "$DNS_THREADS" -retry "$DNS_RETRY" -probe )
if [[ -n "$RESOLVERS_FILE" ]]; then DNS_BASE+=( -r "$RESOLVERS_FILE" ); fi
if [[ "${DNS_RL}" != "0" ]]; then DNS_BASE+=( -rl "$DNS_RL" ); fi

dnsx -l "$OUTDIR/subs.txt" -a    "${DNS_BASE[@]}" -o "$OUTDIR/dns.A.jsonl"
dnsx -l "$OUTDIR/subs.txt" -aaaa "${DNS_BASE[@]}" -o "$OUTDIR/dns.AAAA.jsonl"

# Build resolved host list (probe only live DNS names)
jq -r '.host' "$OUTDIR/dns.A.jsonl" "$OUTDIR/dns.AAAA.jsonl" \
  | sed 's/\.$//' \
  | tr '[:upper:]' '[:lower:]' \
  | awk 'NF' \
  | sort -u > "$OUTDIR/hosts.resolved.txt"

echo "    resolved hosts: $(wc -l < "$OUTDIR/hosts.resolved.txt")"

# ---- 3) Build wildcard test hosts ----
echo "[+] 3) Build wildcard test hostnames per root (${WILDCARD_SAMPLES}/root)"
python3 helpers/make_wildcard_tests.py "$DOMAINS_FILE" "$WILDCARD_SAMPLES" > "$OUTDIR/wild.tests.txt"

# ---- 4) Resolve wildcard test hosts ----
echo "[+] 4) Resolve wildcard test hostnames (DNS wildcard signals)"
dnsx -l "$OUTDIR/wild.tests.txt" -a    "${DNS_BASE[@]}" -o "$OUTDIR/wild.dns.A.jsonl"
dnsx -l "$OUTDIR/wild.tests.txt" -aaaa "${DNS_BASE[@]}" -o "$OUTDIR/wild.dns.AAAA.jsonl"

# ---- 5) HTTP probe (real hosts) ----
echo "[+] 5) HTTP probe resolved hosts (metadata + simhash)"
HTTP_BASE=( -silent -j -t "$HTTP_THREADS" -timeout "$HTTP_TIMEOUT" )
if [[ "${HTTP_RL}" != "0" ]]; then HTTP_BASE+=( -rl "$HTTP_RL" ); fi
if [[ "${HTTP_FOLLOW_REDIRECTS}" == "true" ]]; then HTTP_BASE+=( -fr ); fi

# Use resolved hosts to reduce noise and WAF hits
httpx -l "$OUTDIR/hosts.resolved.txt" "${HTTP_BASE[@]}" \
  -sc -cl -title -location -hash simhash \
  -o "$OUTDIR/httpx.jsonl"

# ---- 6) HTTP probe (wildcard fingerprints) ----
# For wildcard fingerprints, it's often better NOT to follow redirects, so you don’t
# accidentally normalize everything into the same 301/302 chain.
echo "[+] 6) HTTP probe wildcard test hostnames (wildcard HTTP fingerprint)"
HTTP_WILD_BASE=( -silent -j -t "$HTTP_THREADS" -timeout "$HTTP_TIMEOUT" )
if [[ "${HTTP_RL}" != "0" ]]; then HTTP_WILD_BASE+=( -rl "$HTTP_RL" ); fi

httpx -l "$OUTDIR/wild.tests.txt" "${HTTP_WILD_BASE[@]}" \
  -sc -cl -title -location -hash simhash \
  -o "$OUTDIR/wild.httpx.jsonl"

# ---- 7) Classify ----
echo "[+] 7) Merge + classify (non-destructive), produce final + review queues"
python3 helpers/classify_assets.py \
  --domains "$DOMAINS_FILE" \
  --dns-a "$OUTDIR/dns.A.jsonl" \
  --dns-aaaa "$OUTDIR/dns.AAAA.jsonl" \
  --wild-dns-a "$OUTDIR/wild.dns.A.jsonl" \
  --wild-dns-aaaa "$OUTDIR/wild.dns.AAAA.jsonl" \
  --httpx "$OUTDIR/httpx.jsonl" \
  --wild-httpx "$OUTDIR/wild.httpx.jsonl" \
  --outdir "$OUTDIR"

echo "[+] Done."
echo "    Final:  $OUTDIR/final.urls.txt"
echo "    Review: $OUTDIR/review.wildcards.txt"
echo "    All:    $OUTDIR/all.assets.tsv"
echo "[+] Summary:"
echo "    subs:            $(wc -l < "$OUTDIR/subs.txt")"
echo "    resolved:        $(wc -l < "$OUTDIR/hosts.resolved.txt")"
echo "    final keep:      $(wc -l < "$OUTDIR/final.urls.txt" 2>/dev/null || echo 0)"
echo "    review queue:    $(wc -l < "$OUTDIR/review.wildcards.txt" 2>/dev/null || echo 0)"
