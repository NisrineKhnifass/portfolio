from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .compare import compare_scans, format_diff
from .inventory import scan_page
from .rules import check_scan, load_allowed_domains
from .scan_model import external_scripts, inline_scripts

EXIT_OK = 0
EXIT_ISSUES_FOUND = 1
DEFAULT_OUTPUT_PATH = "scan.json"
AUTHORIZATION_REMINDER = "Reminder: only scan sites that you own or are authorized to test."


def load_scan_file(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_scan_file(scan: dict, path: str) -> None:
    Path(path).write_text(json.dumps(scan, indent=2, ensure_ascii=False), encoding="utf-8")


def run_scan_command(arguments: argparse.Namespace) -> int:
    print(AUTHORIZATION_REMINDER, file=sys.stderr)
    scan = scan_page(arguments.url)
    save_scan_file(scan, arguments.output)
    print(
        f"{len(external_scripts(scan))} external script(s), "
        f"{len(inline_scripts(scan))} inline script(s). Scan saved to {arguments.output}"
    )
    return EXIT_OK


def run_compare_command(arguments: argparse.Namespace) -> int:
    old_scan = load_scan_file(arguments.old_scan)
    new_scan = load_scan_file(arguments.new_scan)
    diff = compare_scans(old_scan, new_scan)
    print(format_diff(diff, old_scan, new_scan))
    return EXIT_ISSUES_FOUND if diff.has_changes else EXIT_OK


def run_check_command(arguments: argparse.Namespace) -> int:
    scan = load_scan_file(arguments.scan)
    allowed_domains = load_allowed_domains(arguments.allowlist) if arguments.allowlist else []
    findings = check_scan(scan, allowed_domains)
    if not findings:
        print("No findings.")
        return EXIT_OK
    for finding in findings:
        print(f"[!] {finding.kind}: {finding.target}\n      {finding.detail}")
    return EXIT_ISSUES_FOUND


def add_scan_parser(subparsers) -> None:
    parser = subparsers.add_parser("scan", help="scan a page and save its script inventory as JSON")
    parser.add_argument("url")
    parser.add_argument("-o", "--output", default=DEFAULT_OUTPUT_PATH)
    parser.set_defaults(run=run_scan_command)


def add_compare_parser(subparsers) -> None:
    parser = subparsers.add_parser("compare", help="compare two scans (exit code 1 if they differ)")
    parser.add_argument("old_scan")
    parser.add_argument("new_scan")
    parser.set_defaults(run=run_compare_command)


def add_check_parser(subparsers) -> None:
    parser = subparsers.add_parser(
        "check", help="report unknown domains and obfuscation indicators"
    )
    parser.add_argument("scan")
    parser.add_argument("--allowlist", help="file with one allowed domain per line")
    parser.set_defaults(run=run_check_command)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="magecart-scanner",
        description="Inventory and tamper detection for the scripts of a payment page.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    add_scan_parser(subparsers)
    add_compare_parser(subparsers)
    add_check_parser(subparsers)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_argument_parser().parse_args(argv)
    return arguments.run(arguments)
