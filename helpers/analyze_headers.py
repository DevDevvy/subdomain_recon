#!/usr/bin/env python3
"""Analyze HTTP security headers from httpx results."""
import argparse
import json
from collections import defaultdict
from typing import Dict, List, Set

def iter_jsonl(path: str):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue

# Security headers to check (lowercase)
SECURITY_HEADERS = {
    "strict-transport-security": "HSTS",
    "content-security-policy": "CSP",
    "x-frame-options": "X-Frame-Options",
    "x-content-type-options": "X-Content-Type-Options",
    "x-xss-protection": "X-XSS-Protection",
    "referrer-policy": "Referrer-Policy",
    "permissions-policy": "Permissions-Policy",
    "feature-policy": "Feature-Policy",
}

DANGEROUS_HEADERS = {
    "server": "Server header exposes version",
    "x-powered-by": "X-Powered-By exposes technology",
    "x-aspnet-version": "ASP.NET version exposed",
    "x-aspnetmvc-version": "ASP.NET MVC version exposed",
}

def analyze_headers(httpx_data):
    results = []
    
    for obj in httpx_data:
        url = obj.get("url", "")
        if not url:
            continue
        
        # Get headers (case-insensitive)
        headers_raw = obj.get("header", {}) or obj.get("headers", {})
        headers = {k.lower(): v for k, v in headers_raw.items()}
        
        missing_security = []
        present_security = []
        dangerous_present = []
        
        # Check security headers
        for header_key, header_name in SECURITY_HEADERS.items():
            if header_key in headers:
                present_security.append(f"{header_name}={headers[header_key]}")
            else:
                missing_security.append(header_name)
        
        # Check dangerous headers
        for header_key, issue in DANGEROUS_HEADERS.items():
            if header_key in headers:
                dangerous_present.append(f"{issue}: {headers[header_key]}")
        
        # Calculate security score (0-10)
        score = len(present_security) * 1.25  # Max 10 for 8 headers
        if dangerous_present:
            score -= len(dangerous_present) * 0.5
        score = max(0, min(10, score))
        
        results.append({
            "url": url,
            "score": round(score, 1),
            "missing": ", ".join(missing_security) if missing_security else "None",
            "present": ", ".join(present_security) if present_security else "None",
            "dangerous": ", ".join(dangerous_present) if dangerous_present else "None",
        })
    
    return results

def main(args):
    # Validate and normalize paths to prevent path traversal
    from pathlib import Path
    
    try:
        httpx_path = Path(args.httpx).resolve(strict=True)
        output_path = Path(args.output).resolve()
        
        # Ensure we're working in allowed directories
        if not httpx_path.exists():
            print(f"[!] Error: httpx file not found: {args.httpx}", file=sys.stderr)
            sys.exit(1)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
    except (OSError, RuntimeError) as e:
        print(f"[!] Path validation error: {e}", file=sys.stderr)
        sys.exit(1)
    
    data = list(iter_jsonl(str(httpx_path)))
    results = analyze_headers(data)
    
    # Sort by score (worst first)
    results.sort(key=lambda x: x["score"])
    
    # Write TSV output
    with open(str(output_path), "w", encoding="utf-8") as f:
        f.write("score\turl\tmissing_headers\tpresent_headers\tdangerous_headers\n")
        for r in results:
            f.write(f"{r['score']}\t{r['url']}\t{r['missing']}\t{r['present']}\t{r['dangerous']}\n")
    
    # Print summary
    print(f"[+] Analyzed {len(results)} URLs")
    poor_security = [r for r in results if r['score'] < 5]
    print(f"    URLs with poor security headers (score < 5): {len(poor_security)}")
    
    if poor_security:
        print(f"    Worst offenders:")
        for r in poor_security[:10]:
            print(f"      {r['score']}/10 - {r['url']}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Analyze HTTP security headers")
    ap.add_argument("--httpx", required=True, help="Path to httpx.jsonl file")
    ap.add_argument("--output", required=True, help="Output TSV file")
    main(ap.parse_args())
