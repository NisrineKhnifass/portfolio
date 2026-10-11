from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from .scan_model import external_scripts, short_hash

ALLOWLIST_COMMENT_MARKER = "#"
BASE64_MIN_LENGTH = 200
HEX_ESCAPE_MIN_COUNT = 20

UNKNOWN_DOMAIN = "unknown_domain"
OBFUSCATION_INDICATORS = "obfuscation_indicators"

OBFUSCATION_PATTERNS: dict[str, re.Pattern[str]] = {
    "eval": re.compile(r"\beval\s*\("),
    "atob": re.compile(r"\batob\s*\("),
    "new_function": re.compile(r"\bnew\s+Function\s*\("),
    "from_char_code": re.compile(r"String\.fromCharCode"),
    "long_base64": re.compile(rf"[A-Za-z0-9+/]{{{BASE64_MIN_LENGTH},}}={{0,2}}"),
    "hex_escapes": re.compile(rf"(?:\\x[0-9a-fA-F]{{2}}){{{HEX_ESCAPE_MIN_COUNT},}}"),
}


@dataclass(frozen=True)
class Finding:
    kind: str
    target: str
    detail: str


def find_obfuscation_indicators(source_code: str) -> list[str]:
    return [name for name, pattern in OBFUSCATION_PATTERNS.items() if pattern.search(source_code)]


def load_allowed_domains(path: str | Path) -> list[str]:
    allowed_domains = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        domain = line.split(ALLOWLIST_COMMENT_MARKER, 1)[0].strip().lower()
        if domain:
            allowed_domains.append(domain)
    return allowed_domains


def extract_host(url: str) -> str:
    return urlsplit(url).hostname or ""


def is_same_or_subdomain(host: str, domain: str) -> bool:
    return host == domain or host.endswith("." + domain)


def is_host_allowed(
    host: str, allowed_domains: list[str], first_party_host: str | None = None
) -> bool:
    trusted_domains = list(allowed_domains)
    if first_party_host:
        trusted_domains.append(first_party_host.lower())
    return any(is_same_or_subdomain(host.lower(), domain) for domain in trusted_domains)


def describe_script_target(script: dict) -> str:
    return script.get("url") or f"inline:{short_hash(script['sha256'])}"


def find_unknown_domain_findings(scan: dict, allowed_domains: list[str]) -> list[Finding]:
    first_party_host = extract_host(scan.get("final_url") or scan["url"])
    findings = []
    for script in external_scripts(scan):
        host = extract_host(script["url"])
        if not is_host_allowed(host, allowed_domains, first_party_host):
            findings.append(Finding(UNKNOWN_DOMAIN, script["url"], f"domain not allowed: {host}"))
    return findings


def find_obfuscation_findings(scan: dict) -> list[Finding]:
    return [
        Finding(
            OBFUSCATION_INDICATORS, describe_script_target(script), ", ".join(script["indicators"])
        )
        for script in scan["scripts"]
        if script.get("indicators")
    ]


def check_scan(scan: dict, allowed_domains: list[str]) -> list[Finding]:
    return find_unknown_domain_findings(scan, allowed_domains) + find_obfuscation_findings(scan)
