#!/usr/bin/env python3
"""Classify assets with wildcard detection and tagging."""
import argparse
import json
import sys
from collections import defaultdict, Counter
from typing import Dict, Set, Tuple, Optional
from pathlib import Path

def iter_jsonl(path: str):
    """Safely iterate over JSONL file."""
    if not Path(path).exists():
        print(f"[!] Warning: {path} not found, skipping", file=sys.stderr)
        return
    
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"[!] JSON decode error in {path}:{line_no}: {e}", file=sys.stderr)
                    continue
    except IOError as e:
        print(f"[!] Error reading {path}: {e}", file=sys.stderr)
        return

def read_domains(path: str):
    """Read and normalize domain list."""
    if not Path(path).exists():
        print(f"[!] Error: domains file not found: {path}", file=sys.stderr)
        sys.exit(1)
    
    out = []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.split("#", 1)[0].strip().lower().rstrip(".")
                if line:
                    out.append(line)
    except IOError as e:
        print(f"[!] Error reading domains file: {e}", file=sys.stderr)
        sys.exit(1)
    
    if not out:
        print(f"[!] Error: no domains found in {path}", file=sys.stderr)
        sys.exit(1)
    
    # longest first for suffix matching
    out.sort(key=len, reverse=True)
    return out

def best_root(host: str, roots):
    host = host.lower().rstrip(".")
    for r in roots:
        if host == r or host.endswith("." + r):
            return r
    return None

def dns_ips(obj) -> Set[str]:
    ips = set()
    for k in ("a", "A"):
        v = obj.get(k)
        if isinstance(v, list):
            ips.update(str(x).strip() for x in v if x)
    for k in ("aaaa", "AAAA"):
        v = obj.get(k)
        if isinstance(v, list):
            ips.update(str(x).strip() for x in v if x)
    return {ip for ip in ips if ip}

def get_host(obj) -> str:
    # dnsx/httpx commonly provide "host" in json output
    h = obj.get("host") or ""
    if not h and "url" in obj and isinstance(obj["url"], str) and "://" in obj["url"]:
        h = obj["url"].split("://", 1)[1].split("/", 1)[0]
    return str(h).lower().rstrip(".")

def simhash_int(v) -> Optional[int]:
    if v is None:
        return None
    # httpx prints hash value; for simhash it’s numeric-ish string
    try:
        return int(str(v))
    except ValueError:
        return None

def hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()

def http_sig(obj) -> Tuple[int, str, str, Optional[int], int]:
    sc = int(obj.get("status_code") or 0)
    title = (obj.get("title") or "").strip()
    loc = (obj.get("location") or "").strip()
    sh = simhash_int(obj.get("hash"))
    cl = int(obj.get("content_length") or 0)
    return (sc, title, loc, sh, cl)

def main(args):
    roots = read_domains(args.domains)

    # --- Build DNS maps for real hosts ---
    host_dns: Dict[str, Set[str]] = defaultdict(set)

    for obj in iter_jsonl(args.dns_a):
        host = get_host(obj)
        if host:
            host_dns[host] |= dns_ips(obj)

    for obj in iter_jsonl(args.dns_aaaa):
        host = get_host(obj)
        if host:
            host_dns[host] |= dns_ips(obj)

    # --- Build wildcard DNS fingerprints per root ---
    wild_dns_per_root: Dict[str, Set[str]] = defaultdict(set)

    for obj in iter_jsonl(args.wild_dns_a):
        host = get_host(obj)
        r = best_root(host, roots)
        if r:
            wild_dns_per_root[r] |= dns_ips(obj)

    for obj in iter_jsonl(args.wild_dns_aaaa):
        host = get_host(obj)
        r = best_root(host, roots)
        if r:
            wild_dns_per_root[r] |= dns_ips(obj)

    # --- Build wildcard HTTP fingerprints per root ---
    # We pick the most common signature among wildcard probes for that root.
    wild_http_sigs: Dict[str, Tuple[int, str, str, Optional[int], int]] = {}
    per_root_counter = defaultdict(Counter)

    for obj in iter_jsonl(args.wild_httpx):
        host = get_host(obj)
        r = best_root(host, roots)
        if not r:
            continue
        per_root_counter[r][http_sig(obj)] += 1

    for r, c in per_root_counter.items():
        wild_http_sigs[r] = c.most_common(1)[0][0]

    # --- Parse real httpx results and classify ---
    final_urls = []
    review_urls = []
    rows = []

    SIMHASH_MAX_DIST = args.simhash_max_dist
    CL_TOL_PCT = args.content_length_tol_pct

    def cl_close(a, b):
        if a == 0 or b == 0:
            return False
        lo = min(a, b)
        hi = max(a, b)
        return (hi - lo) / hi <= (CL_TOL_PCT / 100.0)

    for obj in iter_jsonl(args.httpx):
        url = (obj.get("url") or "").strip()
        host = get_host(obj)
        if not host or not url:
            continue

        r = best_root(host, roots)
        dns_ips_set = host_dns.get(host, set())
        wild_dns_set = wild_dns_per_root.get(r or "", set())

        dns_wild_strict = bool(wild_dns_set) and (dns_ips_set == wild_dns_set)
        dns_wild_loose  = bool(wild_dns_set) and (dns_ips_set and dns_ips_set.issubset(wild_dns_set))

        wild_sig = wild_http_sigs.get(r or "")
        sc, title, loc, sh, cl = http_sig(obj)

        http_wild_strong = False
        http_wild_weak = False

        if wild_sig:
            w_sc, w_title, w_loc, w_sh, w_cl = wild_sig

            # strong match: same status AND (same title or same redirect location)
            if sc == w_sc and ((title and title == w_title) or (loc and loc == w_loc)):
                if sh is not None and w_sh is not None:
                    if hamming(sh, w_sh) <= SIMHASH_MAX_DIST:
                        http_wild_strong = True
                    else:
                        http_wild_weak = True
                else:
                    # fallback: content-length closeness when hashes missing
                    http_wild_weak = cl_close(cl, w_cl)

            # weak match: same status and close-ish content length
            elif sc == w_sc and cl_close(cl, w_cl):
                http_wild_weak = True

        # Decision:
        # Only auto-exclude when HTTP wildcard is strong AND DNS wildcard is strict.
        # Everything else goes to review (because false positives are expensive).
        decision = "KEEP"
        if http_wild_strong and dns_wild_strict:
            decision = "EXCLUDE_WILDCARD_STRONG"
            review_urls.append(url)  # still keep in review list
        elif http_wild_strong or dns_wild_loose or http_wild_weak:
            decision = "REVIEW"

        if decision == "KEEP":
            final_urls.append(url)
        else:
            review_urls.append(url)

        rows.append("\t".join([
            host, url,
            str(sc), str(cl),
            title.replace("\t", " "),
            loc.replace("\t", " "),
            "YES" if dns_wild_strict else "NO",
            "YES" if dns_wild_loose else "NO",
            "YES" if http_wild_strong else "NO",
            "YES" if http_wild_weak else "NO",
            decision
        ]))

    # write outputs
    with open(f"{args.outdir}/final.urls.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(set(final_urls))) + "\n")
    with open(f"{args.outdir}/review.wildcards.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(set(review_urls))) + "\n")
    with open(f"{args.outdir}/all.assets.tsv", "w", encoding="utf-8") as f:
        f.write("host\turl\tstatus\tlength\ttitle\tlocation\tdns_wild_strict\tdns_wild_loose\thttp_wild_strong\thttp_wild_weak\tdecision\n")
        f.write("\n".join(rows) + "\n")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--domains", required=True)
    ap.add_argument("--dns-a", required=True)
    ap.add_argument("--dns-aaaa", required=True)
    ap.add_argument("--wild-dns-a", required=True)
    ap.add_argument("--wild-dns-aaaa", required=True)
    ap.add_argument("--httpx", required=True)
    ap.add_argument("--wild-httpx", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--simhash-max-dist", type=int, default=3)
    ap.add_argument("--content-length-tol-pct", type=float, default=5.0)
    main(ap.parse_args())
