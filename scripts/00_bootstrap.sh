#!/usr/bin/env bash
set -euo pipefail

# Ensure we operate relative to recon/ root (not caller's cwd)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing: $1"; exit 1; }; }

need subfinder
need dnsx
need httpx
need jq
need python3

# Required project dirs
mkdir -p input runs output tmp helpers scripts

# Ensure executables are executable
chmod +x bin/recon scripts/*.sh 2>/dev/null || true

echo "[+] OK"
