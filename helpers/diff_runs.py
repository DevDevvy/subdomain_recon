#!/usr/bin/env python3
"""Compare two recon runs and show differences."""
import argparse
import sys
from pathlib import Path

def read_lines(path):
    if not Path(path).exists():
        return set()
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return {line.strip() for line in f if line.strip()}

def main(args):
    from pathlib import Path
    
    # Validate and normalize paths
    try:
        old_dir = Path(args.old).resolve(strict=True)
        new_dir = Path(args.new).resolve(strict=True)
        
        if not old_dir.is_dir():
            print(f"[!] Error: old run directory not found: {args.old}", file=sys.stderr)
            sys.exit(1)
        
        if not new_dir.is_dir():
            print(f"[!] Error: new run directory not found: {args.new}", file=sys.stderr)
            sys.exit(1)
        
    except (OSError, RuntimeError) as e:
        print(f"[!] Path validation error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Compare subdomains
    old_subs = read_lines(old_dir / "subs.txt")
    new_subs = read_lines(new_dir / "subs.txt")
    
    # Compare resolved hosts
    old_hosts = read_lines(old_dir / "hosts.resolved.txt")
    new_hosts = read_lines(new_dir / "hosts.resolved.txt")
    
    # Compare final URLs
    old_urls = read_lines(old_dir / "final.urls.txt")
    new_urls = read_lines(new_dir / "final.urls.txt")
    
    # Compare open ports
    old_ports = read_lines(old_dir / "open.ports.txt")
    new_ports = read_lines(new_dir / "open.ports.txt")
    
    # Calculate differences
    new_subdomains = new_subs - old_subs
    removed_subdomains = old_subs - new_subs
    
    new_resolved = new_hosts - old_hosts
    removed_resolved = old_hosts - new_hosts
    
    new_live_urls = new_urls - old_urls
    removed_live_urls = old_urls - new_urls
    
    new_ports_found = new_ports - old_ports
    removed_ports_found = old_ports - new_ports
    
    # Print comparison report
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║              RECON RUN COMPARISON                            ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
    
    print(f"📂 Comparing:")
    print(f"   Old: {old_dir}")
    print(f"   New: {new_dir}")
    print()
    
    print("📊 SUBDOMAINS")
    print(f"   Old: {len(old_subs):,} | New: {len(new_subs):,}")
    print(f"   ➕ New subdomains:     {len(new_subdomains):,}")
    print(f"   ➖ Removed subdomains:  {len(removed_subdomains):,}")
    print()
    
    print("🔍 RESOLVED HOSTS")
    print(f"   Old: {len(old_hosts):,} | New: {len(new_hosts):,}")
    print(f"   ➕ Newly resolved:     {len(new_resolved):,}")
    print(f"   ➖ No longer resolved: {len(removed_resolved):,}")
    print()
    
    print("🌐 LIVE HTTP/HTTPS")
    print(f"   Old: {len(old_urls):,} | New: {len(new_urls):,}")
    print(f"   ➕ New live URLs:      {len(new_live_urls):,}")
    print(f"   ➖ Dead URLs:          {len(removed_live_urls):,}")
    print()
    
    if old_ports or new_ports:
        print("🔓 OPEN PORTS")
        print(f"   Old: {len(old_ports):,} | New: {len(new_ports):,}")
        print(f"   ➕ New open ports:     {len(new_ports_found):,}")
        print(f"   ➖ Closed ports:       {len(removed_ports_found):,}")
        print()
    
    # Show details if requested
    if args.verbose:
        if new_subdomains:
            print("🆕 NEW SUBDOMAINS:")
            for sub in sorted(new_subdomains)[:50]:
                print(f"   + {sub}")
            if len(new_subdomains) > 50:
                print(f"   ... and {len(new_subdomains) - 50} more")
            print()
        
        if new_live_urls:
            print("🆕 NEW LIVE URLs:")
            for url in sorted(new_live_urls)[:50]:
                print(f"   + {url}")
            if len(new_live_urls) > 50:
                print(f"   ... and {len(new_live_urls) - 50} more")
            print()
        
        if removed_live_urls:
            print("💀 DEAD URLs:")
            for url in sorted(removed_live_urls)[:30]:
                print(f"   - {url}")
            if len(removed_live_urls) > 30:
                print(f"   ... and {len(removed_live_urls) - 30} more")
            print()
    
    # Save diff to files
    if args.output:
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / "new_subdomains.txt", "w") as f:
            f.write("\n".join(sorted(new_subdomains)) + "\n")
        
        with open(output_dir / "new_live_urls.txt", "w") as f:
            f.write("\n".join(sorted(new_live_urls)) + "\n")
        
        with open(output_dir / "removed_live_urls.txt", "w") as f:
            f.write("\n".join(sorted(removed_live_urls)) + "\n")
        
        print(f"💾 Diff files saved to: {output_dir}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Compare two recon runs")
    ap.add_argument("--old", required=True, help="Path to old run directory")
    ap.add_argument("--new", required=True, help="Path to new run directory")
    ap.add_argument("--output", help="Directory to save diff files")
    ap.add_argument("-v", "--verbose", action="store_true", help="Show detailed differences")
    main(ap.parse_args())
