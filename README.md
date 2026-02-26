# Recon — Advanced Bug Bounty Subdomain Enumeration & Validation Pipeline

<div align="center">

**A comprehensive, modular reconnaissance pipeline for bug bounty hunters, penetration testers, and red teamers.**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Bash](https://img.shields.io/badge/bash-5.0%2B-green.svg)](https://www.gnu.org/software/bash/)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)

</div>

---

## 🎯 Overview

This is a production-ready, repeatable recon pipeline designed for bug bounty programs and penetration testing engagements. It provides:

**Core Features:**

- 🔍 **Multi-source subdomain enumeration** (subfinder, amass, assetfinder, crt.sh, and more)
- 🌐 **DNS resolution & validation** (A + AAAA records with custom resolvers)
- 🎭 **Intelligent wildcard detection** (DNS + HTTP fingerprinting)
- 🔬 **HTTP probing with metadata** (status, headers, simhash, tech detection)
- 🎯 **Smart asset classification** (high-confidence targets vs. review queue)

**Advanced Features:**

- 🔓 **Port scanning** (naabu for speed, nmap for deep analysis)
- 🔧 **Technology detection** (httpx, wappalyzer integration)
- 📸 **Screenshot capture** (gowitness, aquatone support)
- 🚨 **Vulnerability scanning** (nuclei, subdomain takeover checks)
- 📊 **Comprehensive reporting** (JSON, TSV, HTML formats)
- 🔄 **Diff mode** (compare runs to track changes)
- 📈 **Statistics & metrics** (visual dashboards and trends)

**Design Philosophy:**

- ✅ **Non-destructive**: Wildcard signals tag and route targets into a review queue rather than deleting assets
- ⚡ **Performance-focused**: Tunable concurrency and rate limiting to respect program rules
- 🛡️ **Security-first**: Built-in security header analysis and vulnerability detection
- 📦 **Modular**: Enable only the features you need via simple configuration

---

## 📋 Table of Contents

- [Requirements](#-requirements)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Workflow](#-workflow)
- [Output Files](#-output-files)
- [Advanced Usage](#-advanced-usage)
- [Utilities](#-utilities)
- [Best Practices](#-best-practices)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)

---

## 🔧 Requirements

### Core Dependencies (Required)

These tools are **required** for basic operation:

```bash
# ProjectDiscovery tools
subfinder    # https://github.com/projectdiscovery/subfinder
dnsx         # https://github.com/projectdiscovery/dnsx
httpx        # https://github.com/projectdiscovery/httpx

# Utilities
jq           # https://stedolan.github.io/jq/
python3      # https://www.python.org/ (3.8+)
```

### Optional Dependencies (Recommended)

Install these for enhanced capabilities:

```bash
# Additional enumeration
amass              # https://github.com/owasp-amass/amass
assetfinder        # https://github.com/tomnomnom/assetfinder
findomain          # https://github.com/Findomain/Findomain
github-subdomains  # https://github.com/gwen001/github-subdomains

# Port scanning
naabu              # https://github.com/projectdiscovery/naabu
nmap               # https://nmap.org/

# Vulnerability scanning
nuclei             # https://github.com/projectdiscovery/nuclei
subzy              # https://github.com/LukaSikic/subzy
subjack            # https://github.com/haccer/subjack

# Technology detection & historical data
waybackurls        # https://github.com/tomnomnom/waybackurls
gau                # https://github.com/lc/gau
unfurl             # https://github.com/tomnomnom/unfurl

# Screenshots
gowitness           # https://github.com/sensepost/gowitness
aquatone            # https://github.com/michenriksen/aquatone

# Additional scanners
nikto               # https://cirt.net/Nikto2
```

### Installation

```bash
# Install ProjectDiscovery suite (core tools)
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest
go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest

# Install additional tools
go install -v github.com/owasp-amass/amass/v4/...@master
go install -v github.com/tomnomnom/assetfinder@latest
go install -v github.com/tomnomnom/waybackurls@latest
go install -v github.com/tomnomnom/unfurl@latest
go install -v github.com/lc/gau/v2/cmd/gau@latest
go install -v github.com/sensepost/gowitness@latest

# Install jq (macOS)
brew install jq

# Install jq (Linux)
sudo apt-get install jq
```

---

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url> recon
cd recon
chmod +x bin/recon scripts/*.sh helpers/*.py
./scripts/00_bootstrap.sh  # Check dependencies
```

### 2. Add Target Domains

Create `input/domains.txt` with your in-scope root domains:

```txt
example.com
example.org
```

### 3. Run Basic Recon

```bash
./bin/recon
```

Or enable all features for comprehensive recon:

```bash
./bin/recon --enable-all
```

### 4. Review Results

```bash
# High-confidence targets (main output)
cat output/final.urls.txt

# Review potential wildcards
cat output/review.wildcards.txt

# View HTML report
open output/report.html
```

---

## ⚙️ Configuration

Create or edit `.env` in the project root to customize behavior:

```bash
# ============================================================================
# CORE SUBDOMAIN ENUMERATION
# ============================================================================
SUBFINDER_FLAGS="-silent -all -recursive"

# ============================================================================
# DNS RESOLUTION
# ============================================================================
DNS_THREADS=200
DNS_RETRY=2
DNS_RL=300                    # queries/sec (set 0 to disable rate limiting)

# Custom resolvers (optional)
# RESOLVERS_FILE="/path/to/resolvers.txt"

# ============================================================================
# HTTP PROBING
# ============================================================================
HTTP_THREADS=75
HTTP_RL=150                   # requests/sec (set 0 to disable)
HTTP_TIMEOUT=10
HTTP_FOLLOW_REDIRECTS=true    # Follow redirects during HTTP probing

# ============================================================================
# WILDCARD DETECTION
# ============================================================================
WILDCARD_SAMPLES=4            # Number of random test hosts per root domain

# ============================================================================
# OPTIONAL FEATURES (set to true to enable)
# ============================================================================

# Additional subdomain enumeration sources
ENABLE_ADDITIONAL_SOURCES=false  # amass, assetfinder, crt.sh, github-subdomains

# Port scanning
ENABLE_PORT_SCAN=false           # Enable naabu/nmap port scanning
NAABU_RATE=1000
NAABU_PORTS="top-ports full"
ENABLE_NMAP=false                # Enable detailed nmap service detection
NMAP_THREADS=50
NMAP_PORTS="top-ports 1000"

# Technology detection & historical data
ENABLE_TECH_DETECT=false         # httpx tech detection, wayback, etc.
ENABLE_SCREENSHOTS=false         # Capture screenshots (gowitness/aquatone)
SCREENSHOT_THREADS=10

# Vulnerability scanning
ENABLE_VULN_SCAN=false           # Run nuclei, subjack, header analysis
NUCLEI_THREADS=50
NUCLEI_RATE=150
NUCLEI_SEVERITY="critical,high,medium"
ENABLE_NIKTO=false               # WARNING: Slow and noisy

# Reporting
ENABLE_HTML_REPORT=true          # Generate HTML report (recommended)

# API Keys (optional, for enhanced results)
# GITHUB_TOKEN="ghp_..."         # For github-subdomains tool
```

### Performance Tuning

**For aggressive scanning:**

```bash
DNS_THREADS=500
DNS_RL=1000
HTTP_THREADS=150
HTTP_RL=300
NAABU_RATE=2000
```

**For stealth/respectful scanning:**

```bash
DNS_THREADS=50
DNS_RL=100
HTTP_THREADS=25
HTTP_RL=50
NAABU_RATE=250
```

---

## 🔄 Workflow

### Phase 1: Subdomain Enumeration

**Default (subfinder only):**

- Uses subfinder with passive sources
- Normalizes output (strips `*.` prefixes, lowercases, dedupes)
- Ensures apex domains are included

**Enhanced (with `ENABLE_ADDITIONAL_SOURCES=true`):**

- Runs: amass, assetfinder, findomain, github-subdomains
- Queries crt.sh certificate transparency logs
- Merges all sources and deduplicates

**Output:**

- `subs.raw.txt` - Raw subfinder output
- `subs.txt` - Cleaned and deduplicated subdomains

### Phase 2: DNS Resolution

- Resolves A and AAAA records using dnsx
- Supports custom resolvers via `RESOLVERS_FILE`
- Respects rate limits and retry logic
- Only live hosts proceed to next phase

**Output:**

- `dns.A.jsonl` - IPv4 records (JSON Lines)
- `dns.AAAA.jsonl` - IPv6 records (JSON Lines)
- `hosts.resolved.txt` - List of resolved hostnames
- `ips.txt` - Unique IP addresses

### Phase 3: Wildcard Detection

**DNS Wildcards:**

- Generates random hostnames (e.g., `a8d7f6xyz.example.com`)
- Resolves them to build wildcard IP fingerprints per root domain

**HTTP Wildcards:**

- Probes random hostnames via HTTP/HTTPS
- Captures response signatures (status, title, simhash)
- Builds wildcard fingerprints for comparison

**Output:**

- `wild.tests.txt` - Random test hostnames
- `wild.dns.A.jsonl`, `wild.dns.AAAA.jsonl` - Wildcard DNS data
- `wild.httpx.jsonl` - Wildcard HTTP responses

### Phase 4: HTTP Probing

- Probes resolved hosts with httpx
- Captures: status code, content length, title, redirect location
- Generates simhash of response body for similarity detection
- Optional: technology detection, CDN identification

**Output:**

- `httpx.jsonl` - HTTP probe results (JSON Lines)
- `httpx.tech.jsonl` - Technology detection (if enabled)

### Phase 5: Classification

Smart classification using wildcard signals:

**Decision Logic:**

- **KEEP**: No wildcard signals → goes to `final.urls.txt`
- **REVIEW**: Weak/partial wildcard signals → goes to `review.wildcards.txt`
- **EXCLUDE_WILDCARD_STRONG**: Strong wildcard match → goes to `review.wildcards.txt`

**Factors Evaluated:**

- DNS IP match (strict and loose)
- HTTP status code similarity
- HTTP title/redirect location matching
- HTTP simhash distance (configurable threshold)
- Content length similarity

**Output:**

- `final.urls.txt` - **High-confidence targets** (primary output)
- `review.wildcards.txt` - **Manual review queue** (potential wildcards)
- `all.assets.tsv` - **Complete inventory** with tags and metadata

### Optional Phase 6: Port Scanning

(Enable with `ENABLE_PORT_SCAN=true`)

- Fast port discovery with naabu
- Optional detailed service detection with nmap
- Scans both IPs and hostnames

**Output:**

- `open.ports.txt` - List of open ports (host:port)
- `ports.naabu.jsonl` - Naabu JSON output
- `nmap.xml`, `nmap.txt` - Nmap results (if enabled)

### Optional Phase 7: Technology Detection

(Enable with `ENABLE_TECH_DETECT=true`)

- Enhanced httpx probing with tech detection
- Wayback URL collection (waybackurls or gau)
- JavaScript file extraction
- URL parameter enumeration
- Optional screenshot capture

**Output:**

- `httpx.tech.jsonl` - Technology detection results
- `wayback.urls.txt` - Historical URLs from Wayback Machine
- `wayback.interesting.txt` - Interesting file extensions
- `js.files.txt` - JavaScript files discovered
- `params.txt` - Unique URL parameters
- `screenshots/` - Screenshots (if enabled)

### Optional Phase 8: Vulnerability Scanning

(Enable with `ENABLE_VULN_SCAN=true`)

- Nuclei vulnerability scanning (customizable severity and templates)
- Subdomain takeover checks (subzy/subjack)
- Security header analysis
- Optional nikto web server scanning

**Output:**

- `vulns/nuclei.jsonl` - Nuclei findings (JSON Lines)
- `vulns/nuclei.summary.tsv` - Human-readable summary
- `vulns/nuclei.stats.txt` - Statistics by severity
- `vulns/subdomain_takeover.json` - Takeover vulnerabilities
- `vulns/security_headers.tsv` - Header analysis

### Reporting & Statistics

- Automatic statistics generation
- HTML report with visual dashboard
- JSON export for programmatic access

**Output:**

- `stats.json` - Detailed statistics
- `report.html` - Interactive HTML dashboard
- `run.log` - Complete execution log

---

## 📊 Output Files

### Primary Outputs

| File                     | Description                                          |
| ------------------------ | ---------------------------------------------------- |
| **final.urls.txt**       | 🎯 High-confidence targets ready for scanning        |
| **review.wildcards.txt** | 🔍 Potential wildcards requiring manual review       |
| **all.assets.tsv**       | 📋 Complete asset inventory with classification tags |

### Supporting Data

| File                            | Description                 |
| ------------------------------- | --------------------------- |
| `subs.txt`                      | Cleaned subdomain list      |
| `hosts.resolved.txt`            | Successfully resolved hosts |
| `ips.txt`                       | Unique IP addresses         |
| `httpx.jsonl`                   | HTTP probing results        |
| `dns.A.jsonl`, `dns.AAAA.jsonl` | DNS resolution data         |

### Advanced Outputs

| File                 | Description                   |
| -------------------- | ----------------------------- |
| `open.ports.txt`     | Open ports (host:port format) |
| `vulns/nuclei.jsonl` | Vulnerability findings        |
| `stats.json`         | Run statistics and metrics    |
| `report.html`        | Interactive HTML dashboard    |
| `run.env`            | Configuration snapshot        |

---

## 🎓 Advanced Usage

### Resume Previous Run

```bash
./bin/recon --resume runs/2026-01-29_164718
```

### Custom Domains File

```bash
./bin/recon --domains /path/to/targets.txt
```

### Enable All Features

```bash
./bin/recon --enable-all
```

### Selective Feature Enablement

Edit `.env`:

```bash
ENABLE_PORT_SCAN=true
ENABLE_VULN_SCAN=true
# Keep ENABLE_TECH_DETECT=false
```

---

## 🛠️ Utilities

### Compare Two Runs (Diff Mode)

Track changes between reconnaissance runs:

```bash
python3 helpers/diff_runs.py \
  --old runs/2026-01-15_120000 \
  --new runs/2026-01-29_164718 \
  --verbose \
  --output diff_output/
```

**Output:**

- Shows new/removed subdomains, hosts, URLs, and ports
- Saves diff files for further analysis
- Perfect for continuous monitoring

### Generate Statistics

```bash
python3 helpers/generate_stats.py --outdir output/
```

Shows:

- Subdomain discovery metrics
- DNS resolution rates
- HTTP status code distribution
- Technology counts
- Vulnerability summary

### Generate HTML Report

```bash
python3 helpers/generate_report.py --outdir output/
```

Creates visual dashboard with:

- Statistics cards
- Status code charts
- Vulnerability tables
- Target lists

### Analyze Security Headers

```bash
python3 helpers/analyze_headers.py \
  --httpx output/httpx.jsonl \
  --output output/security_headers.tsv
```

Identifies:

- Missing security headers (HSTS, CSP, X-Frame-Options, etc.)
- Information disclosure (Server, X-Powered-By)
- Security scores per host

---

## 🛡️ Best Practices

### Program Rules & Ethics

- ✅ **Always respect program scope and rules**
- ✅ **Use conservative rate limits for sensitive programs**
- ✅ **Follow responsible disclosure practices**
- ❌ **Never scan out-of-scope assets**
- ❌ **Avoid aggressive scanning without authorization**

### Performance & Reliability

1. **Start conservative**: Use default settings first
2. **Tune gradually**: Increase concurrency only if needed
3. **Monitor errors**: Check `run.log` for issues
4. **Use custom resolvers**: Avoid DNS provider rate limits
5. **Respect rate limits**: Set `DNS_RL` and `HTTP_RL` appropriately

### Continuous Monitoring

```bash
# Initial baseline
./bin/recon
cp -r output baseline/

# Later scan
./bin/recon

# Compare for changes
python3 helpers/diff_runs.py --old baseline --new output --verbose
```

### Integration with Other Tools

```bash
# Feed results to other tools
cat output/final.urls.txt | tool-name

# Port-specific scanning
grep ':443$' output/open.ports.txt | tool-name

# Extract subdomains by pattern
grep '\.api\.' output/subs.txt > api_subdomains.txt
```

---

## 🐛 Troubleshooting

### No subdomains found

```bash
# Check if subfinder is working
subfinder -d example.com -silent

# Enable additional sources
echo "ENABLE_ADDITIONAL_SOURCES=true" >> .env
```

### DNS rate limiting

```bash
# Reduce DNS rate limit
DNS_RL=100
DNS_THREADS=50

# Use custom resolvers
RESOLVERS_FILE="/path/to/resolvers.txt"
```

### HTTP probing too slow

```bash
# Increase concurrency (carefully)
HTTP_THREADS=100
HTTP_RL=200
```

### Too many wildcards in results

```bash
# Increase wildcard samples for better detection
WILDCARD_SAMPLES=8

# Manually review review.wildcards.txt
# True positives can be moved to final.urls.txt
```

### Missing optional tools

```bash
# Check what's installed
./scripts/00_bootstrap.sh

# Install missing tools as needed
# See Requirements section for links
```

---

## 📈 What's New (v2.0)

### Major Enhancements

✨ **Multi-source enumeration**: Support for 5+ subdomain sources
🔓 **Port scanning**: Integrated naabu and nmap support
🚨 **Vulnerability scanning**: Nuclei, takeover checks, header analysis
📸 **Screenshots**: Automated visual reconnaissance
🔧 **Technology detection**: Comprehensive tech stack identification
📊 **Advanced reporting**: HTML dashboards, statistics, diff mode
⚡ **Performance**: Improved error handling and parallel processing
🎯 **Better classification**: Enhanced wildcard detection logic

### Breaking Changes

None - fully backward compatible with v1.x configurations.

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests if applicable
4. Submit a pull request

### Ideas for Contributions

- Additional subdomain sources integration
- Cloud provider asset discovery (AWS, Azure, GCP)
- Integration with vulnerability databases
- Machine learning for wildcard detection
- Distributed scanning support

---

## ⚠️ Legal Disclaimer

**This tool is for authorized security testing only.**

- Only scan domains you have explicit permission to test
- Respect program rules and rate limits
- Follow responsible disclosure practices
- The authors are not responsible for misuse

---

## 📄 License

MIT License - see LICENSE file for details

---

## 🙏 Acknowledgments

Built with excellent open-source tools:

- [ProjectDiscovery](https://github.com/projectdiscovery) - subfinder, dnsx, httpx, nuclei, naabu
- [OWASP Amass](https://github.com/owasp-amass/amass)
- [Tom Hudson (tomnomnom)](https://github.com/tomnomnom) - waybackurls, unfurl, assetfinder
- And many other amazing security researchers

---

<div align="center">

**Happy Hacking! 🎯🔍**

_Remember: With great power comes great responsibility._

</div>

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
