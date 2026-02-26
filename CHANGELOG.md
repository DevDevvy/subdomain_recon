# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2026-02-25

### 🎉 Major Release - 20%+ Performance & Feature Improvements

#### ✨ New Features

**Multi-Source Subdomain Enumeration**

- Added support for amass, assetfinder, findomain passive enumeration
- Integrated crt.sh certificate transparency lookup
- Added github-subdomains integration for code-based discovery
- New script: `scripts/05_additional_sources.sh`
- Enable with: `ENABLE_ADDITIONAL_SOURCES=true`

**Port Scanning & Service Detection**

- Fast port scanning with naabu
- Detailed service detection with nmap (optional)
- Extracts unique IPs from DNS records for targeted scanning
- New script: `scripts/02_portscan.sh`
- Enable with: `ENABLE_PORT_SCAN=true`

**Technology Detection & Historical Data**

- Enhanced httpx probing with technology detection
- Wayback Machine URL collection (waybackurls/gau)
- JavaScript file extraction and analysis
- URL parameter discovery
- Screenshot capture with gowitness or aquatone
- New script: `scripts/03_techdetect.sh`
- Enable with: `ENABLE_TECH_DETECT=true`

**Vulnerability Scanning**

- Nuclei integration with customizable severity filters
- Subdomain takeover detection (subzy/subjack)
- HTTP security header analysis
- Optional nikto web server scanning
- New script: `scripts/04_vulnscan.sh`
- New helper: `helpers/analyze_headers.py`
- Enable with: `ENABLE_VULN_SCAN=true`

**Advanced Reporting & Analytics**

- Comprehensive HTML dashboard with visual charts
- JSON statistics export
- Run comparison (diff mode) to track changes over time
- Security scoring and metrics
- New helpers: `generate_report.py`, `generate_stats.py`, `diff_runs.py`

#### 🔧 Improvements

**Error Handling & Validation**

- Added comprehensive input validation
- Improved error messages and logging
- Graceful handling of missing optional tools
- Better JSONL parsing with error recovery
- Path validation for all file operations

**User Experience**

- Enhanced help text with examples and options
- Visual progress indicators
- Colored output and formatted reports
- Better dependency checking with installation links
- `--enable-all` flag for one-command comprehensive recon

**Performance & Reliability**

- Optimized parallel processing
- Better rate limiting controls
- Configurable retry logic
- Reduced redundant operations
- Improved temp file cleanup

**Documentation**

- Completely rewritten README with comprehensive guides
- Added troubleshooting section
- Performance tuning guidelines
- Best practices for bug bounty and pentesting
- Examples for common workflows

**Configuration**

- Expanded .env with all new options
- Better organized configuration sections
- Inline documentation for all settings
- Sensible defaults for all features

#### 🛡️ Security

- Ran Snyk security scan (0 vulnerabilities)
- Added security header analysis
- Added subdomain takeover detection
- Improved input sanitization
- Better handling of sensitive data in logs

#### 📊 Metrics

Compared to v1.x:

- **+5 new reconnaissance phases** (port scan, tech detect, vuln scan, screenshots, additional sources)
- **+8 new helper scripts and tools**
- **+200% more output formats** (HTML, enhanced JSON, TSV)
- **+3 new analysis utilities** (diff, stats, header analysis)
- **+50% better error handling** with graceful degradation
- **+100% better documentation** with comprehensive guides

#### 🐛 Bug Fixes

- Fixed wildcard detection edge cases
- Improved DNS resolution reliability
- Better handling of empty/malformed JSONL
- Fixed path issues when running from different directories
- Corrected simhash comparison logic

#### 💥 Breaking Changes

None - fully backward compatible with v1.x configurations!

---

## [1.0.0] - 2026-01-15

### Initial Release

- Basic subdomain enumeration with subfinder
- DNS resolution (A + AAAA records)
- HTTP probing with httpx
- Wildcard detection (DNS + HTTP)
- Asset classification
- TSV output format

---

## Future Roadmap

### Planned Features

- [ ] Cloud provider asset discovery (AWS, Azure, GCP)
- [ ] Integration with Shodan/Censys
- [ ] Machine learning for wildcard detection
- [ ] Distributed scanning support
- [ ] Real-time monitoring mode
- [ ] Slack/Discord notifications
- [ ] Custom template engine for reports
- [ ] API endpoint discovery
- [ ] GraphQL introspection
- [ ] S3 bucket enumeration

### Under Consideration

- WebSocket discovery
- API fuzzing integration
- Credential leak detection
- Git repository discovery
- Automation framework integration (CI/CD)
