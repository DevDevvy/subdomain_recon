#!/usr/bin/env python3
"""Generate HTML report from recon results."""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from collections import Counter

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Recon Report - {run_id}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f0f23;
            color: #cccccc;
            padding: 20px;
            line-height: 1.6;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{
            color: #00d9ff;
            text-align: center;
            margin-bottom: 10px;
            font-size: 2.5em;
            text-shadow: 0 0 10px rgba(0, 217, 255, 0.5);
        }}
        .subtitle {{
            text-align: center;
            color: #888;
            margin-bottom: 40px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: #1a1a2e;
            border: 1px solid #00d9ff;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 0 20px rgba(0, 217, 255, 0.1);
        }}
        .stat-card h3 {{
            color: #00d9ff;
            font-size: 0.9em;
            text-transform: uppercase;
            margin-bottom: 10px;
        }}
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #00ff88;
        }}
        .section {{
            background: #1a1a2e;
            border: 1px solid #333;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 30px;
        }}
        .section h2 {{
            color: #00d9ff;
            margin-bottom: 20px;
            border-bottom: 2px solid #00d9ff;
            padding-bottom: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #333;
        }}
        th {{
            background: #0f0f23;
            color: #00d9ff;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
        }}
        tr:hover {{ background: #252540; }}
        .url {{ color: #00ff88; word-break: break-all; }}
        .status-200 {{ color: #00ff88; }}
        .status-300 {{ color: #ffd700; }}
        .status-400 {{ color: #ff6b6b; }}
        .status-500 {{ color: #ff0000; }}
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: 600;
        }}
        .badge-critical {{ background: #ff0000; color: white; }}
        .badge-high {{ background: #ff6b6b; color: white; }}
        .badge-medium {{ background: #ffd700; color: black; }}
        .badge-low {{ background: #4CAF50; color: white; }}
        .badge-info {{ background: #2196F3; color: white; }}
        .chart {{
            margin-top: 20px;
            padding: 15px;
            background: #0f0f23;
            border-radius: 4px;
        }}
        .bar {{
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }}
        .bar-label {{
            width: 150px;
            font-size: 0.9em;
        }}
        .bar-fill {{
            flex-grow: 1;
            height: 25px;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            border-radius: 4px;
            display: flex;
            align-items: center;
            padding: 0 10px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        .timestamp {{
            text-align: center;
            color: #666;
            margin-top: 40px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Recon Report</h1>
        <div class="subtitle">Run ID: {run_id} | Generated: {timestamp}</div>
        
        <div class="stats-grid">
            {stat_cards}
        </div>
        
        {sections}
        
        <div class="timestamp">
            Report generated on {timestamp}
        </div>
    </div>
</body>
</html>
"""

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

def generate_report(outdir: Path):
    run_id = outdir.name
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Collect statistics
    stats = {
        "Subdomains": len(read_lines(outdir / "subs.txt")),
        "Resolved Hosts": len(read_lines(outdir / "hosts.resolved.txt")),
        "Live HTTP/HTTPS": len(list(iter_jsonl(outdir / "httpx.jsonl"))),
        "Final Targets": len(read_lines(outdir / "final.urls.txt")),
        "Wildcard Review": len(read_lines(outdir / "review.wildcards.txt")),
        "Open Ports": len(read_lines(outdir / "open.ports.txt")),
    }
    
    # Generate stat cards
    stat_cards_html = ""
    for label, value in stats.items():
        if value > 0 or label in ["Subdomains", "Resolved Hosts", "Live HTTP/HTTPS", "Final Targets"]:
            stat_cards_html += f"""
            <div class="stat-card">
                <h3>{label}</h3>
                <div class="stat-value">{value:,}</div>
            </div>
            """
    
    sections_html = ""
    
    # HTTP Status Codes Section
    status_codes = Counter()
    for obj in iter_jsonl(outdir / "httpx.jsonl"):
        status = obj.get("status_code")
        if status:
            status_codes[status] += 1
    
    if status_codes:
        chart_html = '<div class="chart">'
        max_count = max(status_codes.values())
        for status, count in status_codes.most_common(10):
            width_pct = (count / max_count) * 100
            status_class = f"status-{status // 100}00"
            chart_html += f'''
            <div class="bar">
                <div class="bar-label {status_class}">{status}</div>
                <div class="bar-fill" style="width: {width_pct}%;">{count:,}</div>
            </div>
            '''
        chart_html += '</div>'
        
        sections_html += f"""
        <div class="section">
            <h2>📊 HTTP Status Codes</h2>
            {chart_html}
        </div>
        """
    
    # Vulnerabilities Section
    if (outdir / "vulns" / "nuclei.jsonl").exists():
        vulns = list(iter_jsonl(outdir / "vulns" / "nuclei.jsonl"))
        if vulns:
            severity_counts = Counter()
            for v in vulns:
                sev = v.get("info", {}).get("severity", "unknown")
                severity_counts[sev] += 1
            
            table_html = """
            <table>
                <tr>
                    <th>Severity</th>
                    <th>Template</th>
                    <th>Host</th>
                    <th>Matched At</th>
                </tr>
            """
            
            for vuln in vulns[:100]:  # Limit to first 100
                info = vuln.get("info", {})
                sev = info.get("severity", "unknown")
                name = info.get("name", "Unknown")
                host = vuln.get("host", "")
                matched = vuln.get("matched_at", "")
                
                badge_class = f"badge-{sev}"
                table_html += f"""
                <tr>
                    <td><span class="badge {badge_class}">{sev.upper()}</span></td>
                    <td>{name}</td>
                    <td class="url">{host}</td>
                    <td class="url">{matched}</td>
                </tr>
                """
            
            table_html += "</table>"
            
            sections_html += f"""
            <div class="section">
                <h2>🚨 Vulnerabilities ({len(vulns)} findings)</h2>
                <p>Top security findings from Nuclei scanner:</p>
                {table_html}
            </div>
            """
    
    # Final Targets Section
    final_urls = read_lines(outdir / "final.urls.txt")[:100]  # First 100
    if final_urls:
        table_html = "<table><tr><th>#</th><th>URL</th></tr>"
        for i, url in enumerate(final_urls, 1):
            table_html += f'<tr><td>{i}</td><td class="url">{url}</td></tr>'
        table_html += "</table>"
        
        sections_html += f"""
        <div class="section">
            <h2>🎯 Final Targets (Top 100)</h2>
            <p>High-confidence targets ready for deeper scanning:</p>
            {table_html}
        </div>
        """
    
    # Generate final HTML
    html = HTML_TEMPLATE.format(
        run_id=run_id,
        timestamp=timestamp,
        stat_cards=stat_cards_html,
        sections=sections_html
    )
    
    return html

def main(args):
    from pathlib import Path
    
    # Validate and normalize path
    try:
        outdir = Path(args.outdir).resolve(strict=True)
        
        if not outdir.exists():
            print(f"[!] Error: output directory not found: {args.outdir}", file=sys.stderr)
            sys.exit(1)
        
        if not outdir.is_dir():
            print(f"[!] Error: path is not a directory: {args.outdir}", file=sys.stderr)
            sys.exit(1)
    
    except (OSError, RuntimeError) as e:
        print(f"[!] Path validation error: {e}", file=sys.stderr)
        sys.exit(1)
    
    print("[+] Generating HTML report...")
    html = generate_report(outdir)
    
    output_file = outdir / "report.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"[+] Report generated: {output_file}")
    print(f"    Open in browser: file://{output_file.absolute()}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Generate HTML report from recon results")
    ap.add_argument("--outdir", required=True, help="Output directory from recon run")
    main(ap.parse_args())
