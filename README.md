# Recon (Bug Bounty) — Subdomain Enum + Validation Pipeline

This is a small, repeatable recon pipeline for bug bounty programs.

You provide a `domains.txt` (in-scope root domains). One command runs:

1. passive subdomain enumeration
2. DNS resolution (A + AAAA)
3. wildcard detection signals (DNS + HTTP)
4. HTTP probing (metadata + simhash)
5. classification into:
   - `final.urls.txt` (high-confidence targets)
   - `review.wildcards.txt` (needs spot checking)
   - `all.assets.tsv` (everything + tags)

It is designed to be **non-destructive**: wildcard signals are used to **tag and route** targets into a review queue rather than aggressively deleting assets.

---

## Requirements

You need the following tools installed and available in your `$PATH`:

- `subfinder`
- `dnsx`
- `httpx`
- `jq`
- `python3`

> Tip: If you use ProjectDiscovery tooling, make sure you're on reasonably recent versions of `dnsx` and `httpx` so `-json`, `-omit-raw`, and `-hash simhash` work as expected.

---

## Quick Start

1. Add your in-scope root domains:

`input/domains.txt`

```txt
example.com
example.org
```

2. Run:

```bash
cd recon
chmod +x bin/recon scripts/*.sh
./bin/recon
```

Results:

output/final.urls.txt

output/review.wildcards.txt

output/all.assets.tsv

output/run.log

## Configuration (.env)

Create recon/.env to tune performance and rate limits:

```bash
# Subfinder
SUBFINDER_FLAGS="-silent -all -recursive"

# DNS
DNS_THREADS=200
DNS_RETRY=2
DNS_RL=300            # queries/sec (set 0 to disable)

# HTTP
HTTP_THREADS=75
HTTP_RL=150           # requests/sec (set 0 to disable)
HTTP_TIMEOUT=10

# Wildcard fingerprinting
WILDCARD_SAMPLES=4    # random hosts per root domain

# Optional: custom resolvers
# RESOLVERS_FILE="/path/to/resolvers.txt"

# Optional: redirects during main http probe
# HTTP_FOLLOW_REDIRECTS=true
```

bin/recon loads .env automatically if present.

## How It Works (Phase

### 1) Subdomain enumeration (passive)

- Uses subfinder against the roots in domains.txt.
- Normalizes output:
  - strips \*. prefixes
  - removes trailing .
  - lowercases
  - dedupes
- Ensures apex domains (the roots themselves) are included.

Outputs:

- subs.raw.txt
- subs.txt

### 2) DNS resolution

- Resolves A and AAAA using dnsx with JSON output.

Outputs:

- dns.A.jsonl
- dns.AAAA.jsonl
- hosts.resolved.txt

### 3) Wildcard test generation + resolution

- Generates random hostnames per root domain (e.g., as8d7f6...example.com)
- Resolves them to detect DNS wildcard signals.

Outputs:

- wild.tests.txt
- wild.dns.A.jsonl
- wild.dns.AAAA.jsonl

### 4) HTTP probing (real hosts + wildcard tests)

- Probes resolved hosts with httpx and collects:

  - status code, content length, title, redirect location
  - simhash of response body for similarity detection

Outputs:

- httpx.jsonl
- wild.httpx.jsonl

### 5) Classification

helpers/classify_assets.py combines DNS + HTTP data and creates:

- final.urls.txt

High-confidence targets to scan next.

- review.wildcards.txt

Items that match wildcard signals weakly/strongly and should be spot-checked.

- all.assets.tsv

A full table with tags used for auditing and triage.

## Running Again / Finding Results

Each run is stored in:

```
runs/YYYY-MM-DD_HHMMSS/
```

The latest run is always accessible at:

```
output/
```

So you can reference:

- output/final.urls.txt

without remembering timestamps.

### Resume a Previous Run (Optional)

You can “resume” by pointing to an existing run directory:

```
./bin/recon --resume runs/2026-01-07_103012
```

## Safety and Program Rules

- Respect program rate limits and rules.

- Prefer lower concurrency when programs are sensitive.

- This pipeline is designed to reduce unnecessary requests:

  - only probes hosts that resolve via DNS

  - keeps wildcard results in a review queue rather than deleting aggressively

## Warning: This is for use only on sanctioned and approved domains for professional pentesting and bug bounty programs.
