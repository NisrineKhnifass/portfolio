from __future__ import annotations

from dataclasses import dataclass

from .scan_model import external_scripts, inline_scripts, short_hash


@dataclass(frozen=True)
class ScriptChange:
    url: str
    old_sha256: str | None
    new_sha256: str | None


@dataclass(frozen=True)
class HeaderChange:
    name: str
    old_value: str
    new_value: str


@dataclass(frozen=True)
class ScanDiff:
    added_scripts: list[str]
    removed_scripts: list[str]
    changed_scripts: list[ScriptChange]
    added_inline_hashes: list[str]
    removed_inline_hashes: list[str]
    added_headers: list[str]
    removed_headers: list[str]
    changed_headers: list[HeaderChange]

    @property
    def has_changes(self) -> bool:
        return any(
            (
                self.added_scripts,
                self.removed_scripts,
                self.changed_scripts,
                self.added_inline_hashes,
                self.removed_inline_hashes,
                self.added_headers,
                self.removed_headers,
                self.changed_headers,
            )
        )


def index_scripts_by_url(scripts: list[dict]) -> dict[str, dict]:
    return {script["url"]: script for script in scripts}


def collect_inline_hashes(scripts: list[dict]) -> set[str]:
    return {script["sha256"] for script in scripts}


def find_changed_scripts(
    old_scripts: dict[str, dict], new_scripts: dict[str, dict]
) -> list[ScriptChange]:
    shared_urls = sorted(old_scripts.keys() & new_scripts.keys())
    return [
        ScriptChange(url, old_scripts[url]["sha256"], new_scripts[url]["sha256"])
        for url in shared_urls
        if old_scripts[url]["sha256"] != new_scripts[url]["sha256"]
    ]


def find_changed_headers(
    old_headers: dict[str, str], new_headers: dict[str, str]
) -> list[HeaderChange]:
    shared_names = sorted(old_headers.keys() & new_headers.keys())
    return [
        HeaderChange(name, old_headers[name], new_headers[name])
        for name in shared_names
        if old_headers[name] != new_headers[name]
    ]


def compare_scans(old_scan: dict, new_scan: dict) -> ScanDiff:
    old_scripts = index_scripts_by_url(external_scripts(old_scan))
    new_scripts = index_scripts_by_url(external_scripts(new_scan))
    old_inline_hashes = collect_inline_hashes(inline_scripts(old_scan))
    new_inline_hashes = collect_inline_hashes(inline_scripts(new_scan))
    old_headers = old_scan.get("headers", {})
    new_headers = new_scan.get("headers", {})

    return ScanDiff(
        added_scripts=sorted(new_scripts.keys() - old_scripts.keys()),
        removed_scripts=sorted(old_scripts.keys() - new_scripts.keys()),
        changed_scripts=find_changed_scripts(old_scripts, new_scripts),
        added_inline_hashes=sorted(new_inline_hashes - old_inline_hashes),
        removed_inline_hashes=sorted(old_inline_hashes - new_inline_hashes),
        added_headers=sorted(new_headers.keys() - old_headers.keys()),
        removed_headers=sorted(old_headers.keys() - new_headers.keys()),
        changed_headers=find_changed_headers(old_headers, new_headers),
    )


def format_scan_dates(old_scan: dict, new_scan: dict) -> list[str]:
    return [f"Old scan: {old_scan['scanned_at']}", f"New scan: {new_scan['scanned_at']}", ""]


def format_script_lines(diff: ScanDiff) -> list[str]:
    lines = [f"[+] Script added: {url}" for url in diff.added_scripts]
    lines += [f"[-] Script removed: {url}" for url in diff.removed_scripts]
    for change in diff.changed_scripts:
        lines += [
            f"[~] Script CHANGED: {change.url}",
            f"      before: {change.old_sha256}",
            f"      after:  {change.new_sha256}",
        ]
    return lines


def format_inline_lines(diff: ScanDiff) -> list[str]:
    lines = [
        f"[+] Inline script added (sha256 {short_hash(sha256)}...)"
        for sha256 in diff.added_inline_hashes
    ]
    lines += [
        f"[-] Inline script removed (sha256 {short_hash(sha256)}...)"
        for sha256 in diff.removed_inline_hashes
    ]
    return lines


def format_header_lines(diff: ScanDiff) -> list[str]:
    lines = [f"[+] Header added: {name}" for name in diff.added_headers]
    lines += [f"[-] Header removed: {name}" for name in diff.removed_headers]
    lines += [f"[~] Header changed: {change.name}" for change in diff.changed_headers]
    return lines


def format_diff(diff: ScanDiff, old_scan: dict, new_scan: dict) -> str:
    lines = format_scan_dates(old_scan, new_scan)
    if not diff.has_changes:
        return "\n".join(lines + ["No changes detected."])
    lines += format_script_lines(diff) + format_inline_lines(diff) + format_header_lines(diff)
    return "\n".join(lines)
