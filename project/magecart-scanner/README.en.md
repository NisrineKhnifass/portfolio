# Magecart Scanner

[Version française](README.md)

Prototype of a tool that **inventories the scripts on an e-commerce payment page** and **detects when one of them changes**, to help meet **PCI DSS 4.0 requirements 6.4.3** (script inventory, justification and integrity) and **11.6.1** (detection of changes to HTTP headers and payment page content).

> **Status: v0.1 prototype, personal project in progress.** See [what is done and what remains](#status).

## Why

Magecart (web skimming) steals card data directly in the customer's browser, through a compromised third-party script on the payment page. Server-side controls cannot see what runs in the browser. The long-term goal is a simple tool that a small business without a security team can use (for example as a WooCommerce plugin).

Project presentation (slides): [FR](docs/magecart-presentation-fr.pdf) · [EN](docs/magecart-presentation-en.pdf)

## What v0.1 does

- **Inventory**: Playwright loads the page in Chromium, lists external and inline scripts (including dynamically loaded ones) and computes a **SHA-256** fingerprint of each.
- **HTTP headers**: records the page's security headers (CSP, HSTS, etc.).
- **Comparison**: compares two scans and reports scripts that were added, removed or **modified**, as well as modified headers.
- **Allowlist**: flags scripts loaded from a domain that is not allowed.
- **Indicators**: spots signs of obfuscation (`eval`, `atob`, `new Function`, long base64 strings...). These are **signals to review**, not proof: legitimate minified code can trigger them.

## Installation

Python 3.10 or later.

```bash
git clone https://github.com/NisrineKhnifass/portfolio.git
cd portfolio/project/magecart-scanner
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
playwright install chromium
```

## Usage

```bash
magecart-scanner scan https://example.test/checkout -o scan1.json   # inventory
magecart-scanner scan https://example.test/checkout -o scan2.json   # later
magecart-scanner compare scan1.json scan2.json                      # differences (exit code 1 if any)
magecart-scanner check scan2.json --allowlist domains.txt           # unknown domains, indicators
```

`domains.txt`: one allowed domain per line (`#` for comments). The scanned page's own domain is always allowed, and an allowed domain covers its subdomains.

> **Only scan sites that you own or that you are authorized to test.**

## Try it on the local test bench

The `testbench/` folder contains a fake payment page and a **harmless** fake third-party script (two versions, one of them modified). No real payment, no data-stealing code.

```bash
python testbench/serve.py                                  # terminal 1: shop (8000) + third-party domain (8001)

magecart-scanner scan http://127.0.0.1:8000/ -o scan1.json # terminal 2
curl http://localhost:8001/__variant/v2                    # the fake third-party script changes
magecart-scanner scan http://127.0.0.1:8000/ -o scan2.json
magecart-scanner compare scan1.json scan2.json
```

Expected result:

```
[~] Script CHANGED: http://localhost:8001/analytics.js
      before: 981975a4...
      after:  47626030...
```

The third-party script is served from `localhost` while the page is scanned through `127.0.0.1`: these are two different hosts, so `magecart-scanner check scan1.json` flags it as an unauthorized domain, and `--allowlist testbench/allowlist.txt` declares it allowed.

## Tests and code quality

```bash
pytest                     # all tests (the end-to-end test launches Chromium)
pytest -m "not browser"    # unit tests only
ruff check . && ruff format --check .
```

## Code conventions

- English code without comments: function and variable names describe what they do.
- Short functions that do one thing, no "magic" values (thresholds are named constants).
- Logic that does not need the browser (`build_scan`, `compare_scans`, `check_scan`) is separated from the Playwright part, so it can be tested without Chromium.

## Status

| Feature | State |
| --- | --- |
| Script inventory + SHA-256 | done (v0.1) |
| Comparison of two scans, HTTP headers | done (v0.1) |
| Domain allowlist, obfuscation indicators | done (v0.1, simple rules) |
| Local test bench | done (v0.1, script modification scenario) |
| Suspicious outbound requests | upcoming |
| Alerts (email, Slack / Discord webhook) | upcoming |
| Exportable, timestamped compliance report | upcoming |
| WooCommerce plugin | upcoming |
| Real-time in-browser monitoring (MutationObserver) | idea for phase 2 |

## Limitations

- A modified **inline** script appears as "removed" then "added" (it has no stable identifier).
- A periodic scan **does not replace continuous monitoring**: a script can change between two scans, or misbehave only for some visitors.
- The obfuscation indicators produce **false positives**.
- This tool **helps prepare for compliance** but does not replace the assessment of a qualified assessor (QSA).

## License

MIT, see [LICENSE](LICENSE).
