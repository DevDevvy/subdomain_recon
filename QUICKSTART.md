# Quick Start Guide

Get started with recon in under 5 minutes!

## 📦 Installation

### 1. Install Core Dependencies

```bash
# Install Go (if not already installed)
# macOS:
brew install go

# Linux:
# Follow https://go.dev/doc/install

# Add Go bin to PATH
export PATH=$PATH:$(go env GOPATH)/bin
```

### 2. Install Required Tools

```bash
# Core tools (required)
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest

# Install jq
# macOS:
brew install jq

# Linux:
sudo apt-get install jq

# Python 3 (usually pre-installed)
python3 --version
```

### 3. Install Optional Tools (Recommended)

```bash
# Vulnerability scanning
go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest

# Port scanning
go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest

# Additional enumeration
go install -v github.com/owasp-amass/amass/v4/...@master
go install -v github.com/tomnomnom/assetfinder@latest

# Technology detection & wayback
go install -v github.com/tomnomnom/waybackurls@latest
go install -v github.com/lc/gau/v2/cmd/gau@latest

# Screenshots
go install -v github.com/sensepost/gowitness@latest
```

## 🚀 First Run

### 1. Clone and Setup

```bash
git clone <repository-url> recon
cd recon
chmod +x bin/recon scripts/*.sh helpers/*.py
```

### 2. Check Dependencies

```bash
./scripts/00_bootstrap.sh
```

This will show which tools are installed and which are missing.

### 3. Add Your Targets

Create `input/domains.txt`:

```txt
example.com
example.net
```

### 4. Run Basic Recon

```bash
./bin/recon
```

### 5. View Results

```bash
# Most important: high-confidence targets
cat output/final.urls.txt

# Review potential wildcards manually
cat output/review.wildcards.txt

# Open visual HTML report
open output/report.html

# View statistics
cat output/stats.json
```

## ⚡ Quick Commands

### Basic Scan

```bash
./bin/recon
```

### Comprehensive Scan (All Features)

```bash
./bin/recon --enable-all
```

Or edit `.env`:

```bash
ENABLE_ADDITIONAL_SOURCES=true
ENABLE_PORT_SCAN=true
ENABLE_TECH_DETECT=true
ENABLE_VULN_SCAN=true
```

Then run:

```bash
./bin/recon
```

### Custom Domains File

```bash
./bin/recon --domains /path/to/my-targets.txt
```

### Resume Previous Run

```bash
./bin/recon --resume runs/2026-01-29_164718
```

## 📊 Understanding Output

### Key Files

1. **`output/final.urls.txt`** ← START HERE
   - Ready-to-scan targets with high confidence
   - Feed these to your scanners (nuclei, ffuf, etc.)

2. **`output/review.wildcards.txt`**
   - Potential wildcard matches
   - Manually review these to find hidden gems
   - Some may be false positives

3. **`output/report.html`**
   - Visual dashboard
   - Statistics and charts
   - Vulnerability summary

4. **`output/all.assets.tsv`**
   - Complete asset inventory
   - Includes all metadata and tags
   - Good for auditing

### Using Results with Other Tools

```bash
# Feed to nuclei
cat output/final.urls.txt | nuclei -t cves/

# Feed to ffuf
cat output/final.urls.txt | while read url; do
  ffuf -u "$url/FUZZ" -w wordlist.txt
done

# Extract specific subdomains
grep 'api' output/subs.txt
grep 'admin' output/subs.txt
grep 'dev\|staging\|test' output/subs.txt

# Export open ports
cat output/open.ports.txt
```

## ⚙️ Configuration Tips

### For Bug Bounty Programs

```bash
# In .env
DNS_THREADS=100
DNS_RL=200
HTTP_THREADS=50
HTTP_RL=100
ENABLE_VULN_SCAN=true
ENABLE_TECH_DETECT=true
```

### For Internal Pentests (Faster)

```bash
# In .env
DNS_THREADS=500
DNS_RL=1000
HTTP_THREADS=150
HTTP_RL=300
ENABLE_PORT_SCAN=true
ENABLE_NMAP=true
ENABLE_VULN_SCAN=true
```

### For Stealth/Respectful Scanning

```bash
# In .env
DNS_THREADS=25
DNS_RL=50
HTTP_THREADS=20
HTTP_RL=30
```

## 🔄 Continuous Monitoring

Set up automated scanning to track changes:

```bash
# Day 1: Baseline
./bin/recon
cp -r output/ baseline/

# Day 7: Check for changes
./bin/recon

# Compare runs
python3 helpers/diff_runs.py \
  --old baseline \
  --new output \
  --verbose \
  --output diffs/

# Review new findings
cat diffs/new_live_urls.txt
```

## 📖 Next Steps

1. Read the full [README.md](README.md) for detailed documentation
2. Check [CHANGELOG.md](CHANGELOG.md) for latest features
3. Tune `.env` settings for your use case
4. Explore optional features (port scanning, vuln scanning, etc.)

## 🆘 Need Help?

### Common Issues

**"No subdomains found"**

```bash
# Test subfinder directly
subfinder -d example.com -silent

# Enable additional sources
echo "ENABLE_ADDITIONAL_SOURCES=true" >> .env
```

**"DNS resolution failing"**

```bash
# Use custom resolvers
RESOLVERS_FILE="/path/to/resolvers.txt"

# Reduce rate limits
DNS_RL=100
DNS_THREADS=50
```

**"Too many wildcards"**

```bash
# Increase wildcard samples for better detection
WILDCARD_SAMPLES=8

# Manually review review.wildcards.txt
# Move false positives to final.urls.txt manually
```

### Getting More Help

- Check the [Troubleshooting](README.md#-troubleshooting) section
- Review error messages in `output/run.log`
- Ensure all dependencies are installed: `./scripts/00_bootstrap.sh`

---

**Happy Hacking! 🎯**

Remember: Only scan domains you have permission to test!
