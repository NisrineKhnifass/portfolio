from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urldefrag

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from . import __version__
from .rules import find_obfuscation_indicators
from .scan_model import EXTERNAL_SCRIPT, INLINE_SCRIPT

DEFAULT_TIMEOUT_MS = 30_000
SCRIPT_RESOURCE_TYPE = "script"
MODULE_SCRIPT_TYPE = "module"
JAVASCRIPT_TYPE_KEYWORD = "javascript"

TRACKED_SECURITY_HEADERS = (
    "content-security-policy",
    "content-security-policy-report-only",
    "strict-transport-security",
    "x-frame-options",
    "x-content-type-options",
    "referrer-policy",
    "permissions-policy",
)

COLLECT_DOM_SCRIPTS_JS = """
() => Array.from(document.querySelectorAll('script')).map(script => ({
  src: script.src || null,
  integrity: script.getAttribute('integrity'),
  type: script.getAttribute('type'),
  text: script.src ? null : script.textContent
}))
"""

NetworkScripts = dict[str, tuple[int | None, bytes | None]]


@dataclass
class PageSnapshot:
    final_url: str
    response_headers: dict[str, str]
    dom_scripts: list[dict]
    network_scripts: NetworkScripts


def sha256_of(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def strip_fragment(url: str) -> str:
    return urldefrag(url)[0]


def current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def is_executable_script_type(script_type: str | None) -> bool:
    normalized_type = (script_type or "").strip().lower()
    return (
        normalized_type == ""
        or normalized_type == MODULE_SCRIPT_TYPE
        or JAVASCRIPT_TYPE_KEYWORD in normalized_type
    )


def decode_source_code(content: bytes | None) -> str:
    return content.decode("utf-8", errors="ignore") if content else ""


def filter_tracked_headers(headers: dict[str, str]) -> dict[str, str]:
    return {name: value for name, value in headers.items() if name in TRACKED_SECURITY_HEADERS}


def describe_external_script(
    url: str, status: int | None, body: bytes | None, integrity: str | None, is_in_dom: bool
) -> dict:
    return {
        "kind": EXTERNAL_SCRIPT,
        "url": url,
        "status": status,
        "sha256": sha256_of(body) if body is not None else None,
        "size": len(body) if body is not None else None,
        "integrity": integrity,
        "in_dom": is_in_dom,
        "indicators": find_obfuscation_indicators(decode_source_code(body)),
    }


def describe_inline_script(source_code: str) -> dict:
    content = source_code.encode("utf-8")
    return {
        "kind": INLINE_SCRIPT,
        "sha256": sha256_of(content),
        "size": len(content),
        "indicators": find_obfuscation_indicators(source_code),
    }


def describe_dom_script(dom_script: dict, network_scripts: NetworkScripts) -> dict | None:
    if not is_executable_script_type(dom_script.get("type")):
        return None
    if dom_script.get("src"):
        url = strip_fragment(dom_script["src"])
        status, body = network_scripts.get(url, (None, None))
        return describe_external_script(url, status, body, dom_script.get("integrity"), True)
    return describe_inline_script(dom_script.get("text") or "")


def describe_scripts_missing_from_dom(
    network_scripts: NetworkScripts, urls_in_dom: set[str]
) -> list[dict]:
    return [
        describe_external_script(url, status, body, None, False)
        for url, (status, body) in network_scripts.items()
        if url not in urls_in_dom
    ]


def build_scan(
    url: str,
    final_url: str,
    headers: dict[str, str],
    dom_scripts: list[dict],
    network_scripts: NetworkScripts,
    scanned_at: str | None = None,
) -> dict:
    described_dom_scripts = [
        described
        for described in (describe_dom_script(script, network_scripts) for script in dom_scripts)
        if described is not None
    ]
    urls_in_dom = {
        script["url"] for script in described_dom_scripts if script["kind"] == EXTERNAL_SCRIPT
    }
    return {
        "tool": "magecart-scanner",
        "version": __version__,
        "scanned_at": scanned_at or current_timestamp(),
        "url": url,
        "final_url": final_url,
        "headers": filter_tracked_headers(headers),
        "scripts": described_dom_scripts
        + describe_scripts_missing_from_dom(network_scripts, urls_in_dom),
    }


def read_body_or_none(response) -> bytes | None:
    try:
        return response.body()
    except PlaywrightError:
        return None


def make_script_response_recorder(network_scripts: NetworkScripts):
    def record_script_response(response) -> None:
        if response.request.resource_type != SCRIPT_RESOURCE_TYPE:
            return
        network_scripts[strip_fragment(response.url)] = (
            response.status,
            read_body_or_none(response),
        )

    return record_script_response


def lowercase_keys(headers: dict[str, str]) -> dict[str, str]:
    return {name.lower(): value for name, value in headers.items()}


def capture_page_snapshot(url: str, timeout_ms: int) -> PageSnapshot:
    network_scripts: NetworkScripts = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.on("response", make_script_response_recorder(network_scripts))
            main_response = page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            return PageSnapshot(
                final_url=page.url,
                response_headers=lowercase_keys(main_response.headers) if main_response else {},
                dom_scripts=page.evaluate(COLLECT_DOM_SCRIPTS_JS),
                network_scripts=network_scripts,
            )
        finally:
            browser.close()


def scan_page(url: str, timeout_ms: int = DEFAULT_TIMEOUT_MS) -> dict:
    snapshot = capture_page_snapshot(url, timeout_ms)
    return build_scan(
        url,
        snapshot.final_url,
        snapshot.response_headers,
        snapshot.dom_scripts,
        snapshot.network_scripts,
    )
