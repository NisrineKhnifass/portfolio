from magecart_scanner.rules import (
    Finding,
    check_scan,
    find_obfuscation_indicators,
    is_host_allowed,
    load_allowed_domains,
)


def test_finds_obfuscation_indicators():
    assert find_obfuscation_indicators("var decoded = eval(atob('abc'));") == ["eval", "atob"]


def test_finds_no_indicator_in_plain_code():
    assert find_obfuscation_indicators("console.log('hello')") == []


def test_finds_long_base64_string():
    assert "long_base64" in find_obfuscation_indicators("var payload = '" + "A" * 250 + "';")


def test_allowed_domain_covers_itself_and_its_subdomains():
    assert is_host_allowed("example.com", ["example.com"])
    assert is_host_allowed("cdn.example.com", ["example.com"])


def test_allowed_domain_does_not_cover_lookalike_hosts():
    assert not is_host_allowed("evilexample.com", ["example.com"])
    assert not is_host_allowed("example.com.evil.net", ["example.com"])


def test_first_party_host_is_always_allowed():
    assert is_host_allowed("shop.test", [], first_party_host="shop.test")


def test_load_allowed_domains_ignores_blank_lines_and_comments(tmp_path):
    allowlist_file = tmp_path / "allowlist.txt"
    allowlist_file.write_text("Example.com\n\n# ignored\ncdn.test # trailing\n", encoding="utf-8")

    assert load_allowed_domains(allowlist_file) == ["example.com", "cdn.test"]


def test_check_scan_reports_unknown_domain_and_obfuscation():
    scan = {
        "url": "https://shop.test/pay",
        "scripts": [
            {
                "kind": "external",
                "url": "https://shop.test/app.js",
                "sha256": "1",
                "indicators": [],
            },
            {
                "kind": "external",
                "url": "https://cdn.good.com/lib.js",
                "sha256": "2",
                "indicators": [],
            },
            {
                "kind": "external",
                "url": "https://unknown.net/t.js",
                "sha256": "3",
                "indicators": ["eval"],
            },
        ],
    }

    findings = check_scan(scan, ["good.com"])

    assert findings == [
        Finding("unknown_domain", "https://unknown.net/t.js", "domain not allowed: unknown.net"),
        Finding("obfuscation_indicators", "https://unknown.net/t.js", "eval"),
    ]
