#!/usr/bin/env python3
"""Generate statistics and metrics from a recon run."""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

def iter_jsonl(path):
    if not Path(path).exists():
        return
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue

def read_lines(path):
    if not Path(path).exists():
        return []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return [line.strip() for line in f if line.strip()]

def main(args):
    from pathlib import Path
    
    # Validate and normalize path
    try:
        outdir = Path(args.outdir).resolve(strict=True)
        
        if not outdir.is_dir():
            print(f"[!] Error: output directory not found: {args.outdir}", file=sys.stderr)
            sys.exit(1)
    
    except (OSError, RuntimeError) as e:
        print(f"[!] Path validation error: {e}", file=sys.stderr)
        sys.exit(1)
    
    stats = {
        "subdomains": {
            "raw": len(read_lines(outdir / "subs.raw.txt")),
            "cleaned": len(read_lines(outdir / "subs.txt")),
        },
        "dns": {
            "resolved": len(read_lines(outdir / "hosts.resolved.txt")),
            "a_records": len(list(iter_jsonl(outdir / "dns.A.jsonl"))),
            "aaaa_records": len(list(iter_jsonl(outdir / "dns.AAAA.jsonl"))),
        },
        "http": {
            "live": len(list(iter_jsonl(outdir / "httpx.jsonl"))),
            "final_targets": len(read_lines(outdir / "final.urls.txt")),
            "wildcard_review": len(read_lines(outdir / "review.wildcards.txt")),
        },
        "status_codes": Counter(),
        "technologies": Counter(),
        "ports": {
            "open": len(read_lines(outdir / "open.ports.txt")),
        },
        "vulnerabilities": {
            "nuclei": len(list(iter_jsonl(outdir / "vulns" / "nuclei.jsonl"))),
        },
    }
    
    # Analyze HTTP status codes
    for obj in iter_jsonl(outdir / "httpx.jsonl"):
        status = obj.get("status_code")
        if status:
            stats["status_codes"][status] += 1
        
        # Extract technologies if available
        tech = obj.get("tech") or obj.get("technologies")
        if tech:
            if isinstance(tech, list):
                for t in tech:
                    stats["technologies"][t] += 1
            elif isinstance(tech, str):
                stats["technologies"][tech] += 1
    
    # Analyze nuclei by severity
    nuclei_severity = Counter()
    for obj in iter_jsonl(outdir / "vulns" / "nuclei.jsonl"):
        sev = obj.get("info", {}).get("severity", "unknown")
        nuclei_severity[sev] += 1
    
    # Print statistics report
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║              RECON PIPELINE STATISTICS                       ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    
    print("📊 SUBDOMAIN ENUMERATION")
    print(f"   Raw subdomains discovered:  {stats['subdomains']['raw']:,}")
    print(f"   Cleaned & deduplicated:     {stats['subdomains']['cleaned']:,}")
    print()
    
    print("🔍 DNS RESOLUTION")
    print(f"   Hosts resolved:             {stats['dns']['resolved']:,}")
    print(f"   IPv4 (A) records:           {stats['dns']['a_records']:,}")
    print(f"   IPv6 (AAAA) records:        {stats['dns']['aaaa_records']:,}")
    print()
    
    print("🌐 HTTP PROBING")
    print(f"   Live HTTP/HTTPS hosts:      {stats['http']['live']:,}")
    print(f"   Final targets (high conf):  {stats['http']['final_targets']:,}")
    print(f"   Wildcard review queue:      {stats['http']['wildcard_review']:,}")
    print()
    
    if stats['status_codes']:
        print("📋 HTTP STATUS CODES (Top 10)")
        for status, count in stats['status_codes'].most_common(10):
            print(f"   {status}: {count:,}")
        print()
    
    if stats['technologies']:
        print("🔧 TECHNOLOGIES DETECTED (Top 15)")
        for tech, count in stats['technologies'].most_common(15):
            print(f"   {tech}: {count:,}")
        print()
    
    if stats['ports']['open'] > 0:
        print("🔓 PORT SCANNING")
        print(f"   Open ports found:           {stats['ports']['open']:,}")
        print()
    
    if stats['vulnerabilities']['nuclei'] > 0:
        print("🚨 VULNERABILITY SCANNING")
        print(f"   Total nuclei findings:      {stats['vulnerabilities']['nuclei']:,}")
        if nuclei_severity:
            print("   By severity:")
            for sev in ['critical', 'high', 'medium', 'low', 'info']:
                if sev in nuclei_severity:
                    print(f"      {sev.upper()}: {nuclei_severity[sev]:,}")
        print()
    
    # Calculate discovery rate
    if stats['subdomains']['cleaned'] > 0:
        resolution_rate = (stats['dns']['resolved'] / stats['subdomains']['cleaned']) * 100
        live_rate = (stats['http']['live'] / stats['dns']['resolved']) * 100 if stats['dns']['resolved'] > 0 else 0
        
        print("📈 DISCOVERY RATES")
        print(f"   DNS resolution rate:        {resolution_rate:.1f}%")
        print(f"   HTTP live rate:             {live_rate:.1f}%")
        print()
    
    # Save statistics to JSON
    stats_file = outdir / "stats.json"
    stats_output = {
        "subdomains": stats["subdomains"],
        "dns": stats["dns"],
        "http": stats["http"],
        "status_codes": dict(stats["status_codes"]),
        "technologies": dict(stats["technologies"].most_common(50)),
        "ports": stats["ports"],
        "vulnerabilities": {
            "nuclei_total": stats["vulnerabilities"]["nuclei"],
            "nuclei_by_severity": dict(nuclei_severity),
        },
    }
    
    with open(stats_file, "w") as f:
        json.dump(stats_output, f, indent=2)
    
    print(f"💾 Detailed statistics saved to: {stats_file}")
    print()

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Generate recon statistics")
    ap.add_argument("--outdir", required=True, help="Output directory from recon run")
    main(ap.parse_args())
