#!/usr/bin/env bash
set -euo pipefail

# Ensure we operate relative to recon/ root (not caller's cwd)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

echo "[+] Checking dependencies..."

# Core required tools
REQUIRED=(
  "subfinder:https://github.com/projectdiscovery/subfinder"
  "dnsx:https://github.com/projectdiscovery/dnsx"
  "httpx:https://github.com/projectdiscovery/httpx"
  "jq:https://stedolan.github.io/jq/"
  "python3:https://www.python.org/"
)

# Optional but recommended tools
OPTIONAL=(
  "nuclei:https://github.com/projectdiscovery/nuclei"
  "naabu:https://github.com/projectdiscovery/naabu"
  "amass:https://github.com/owasp-amass/amass"
  "assetfinder:https://github.com/tomnomnom/assetfinder"
  "waybackurls:https://github.com/tomnomnom/waybackurls"
  "gau:https://github.com/lc/gau"
  "gowitness:https://github.com/sensepost/gowitness"
  "unfurl:https://github.com/tomnomnom/unfurl"
  "findomain:https://github.com/Findomain/Findomain"
  "github-subdomains:https://github.com/gwen001/github-subdomains"
  "subzy:https://github.com/LukaSikic/subzy"
  "subjack:https://github.com/haccer/subjack"
  "aquatone:https://github.com/michenriksen/aquatone"
  "nmap:https://nmap.org/"
  "nikto:https://cirt.net/Nikto2"
)

need() { 
  local cmd="$1"
  local url="$2"
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "  ✓ $cmd"
    return 0
  else
    echo "  ✗ $cmd (not found)"
    if [[ -n "$url" ]]; then
      echo "    Install: $url"
    fi
    return 1
  fi
}

echo ""
echo "Core Dependencies (required):"
MISSING_CORE=0
for item in "${REQUIRED[@]}"; do
  IFS=':' read -r cmd url <<< "$item"
  need "$cmd" "$url" || ((MISSING_CORE++))
done

echo ""
echo "Optional Dependencies (recommended for enhanced features):"
MISSING_OPTIONAL=0
for item in "${OPTIONAL[@]}"; do
  IFS=':' read -r cmd url <<< "$item"
  need "$cmd" "$url" || ((MISSING_OPTIONAL++)) || true
done

echo ""

if [[ $MISSING_CORE -gt 0 ]]; then
  echo "[!] ERROR: Missing $MISSING_CORE core dependencies. Please install them and try again."
  exit 1
fi

if [[ $MISSING_OPTIONAL -gt 0 ]]; then
  echo "[!] Note: $MISSING_OPTIONAL optional tools not found."
  echo "    Some features will be disabled. Install them for enhanced recon capabilities."
  echo ""
fi

# Required project dirs
mkdir -p input runs output tmp helpers scripts

# Ensure executables are executable
chmod +x bin/recon scripts/*.sh helpers/*.py 2>/dev/null || true

echo "[+] Bootstrap complete."
echo ""
