import hashlib

from magecart_scanner.inventory import (
    build_scan,
    is_executable_script_type,
    sha256_of,
    strip_fragment,
)


def test_sha256_of_matches_hashlib():
    assert sha256_of(b"abc") == hashlib.sha256(b"abc").hexdigest()


def test_strip_fragment_removes_the_anchor():
    assert strip_fragment("https://a.com/x.js#top") == "https://a.com/x.js"


def test_data_blocks_are_not_executable_scripts():
    assert is_executable_script_type(None)
    assert is_executable_script_type("module")
    assert is_executable_script_type("text/javascript")
    assert not is_executable_script_type("application/ld+json")


def build_sample_scan():
    dom_scripts = [
        {"src": "https://a.com/x.js", "integrity": "sha384-abc", "type": None, "text": None},
        {"src": None, "integrity": None, "type": None, "text": "var a = 1;"},
        {"src": None, "integrity": None, "type": "application/ld+json", "text": "{}"},
    ]
    network_scripts = {
        "https://a.com/x.js": (200, b"console.log(1)"),
        "https://dynamic.net/d.js": (200, b"eval('1')"),
    }
    headers = {"x-frame-options": "DENY", "server": "nginx"}
    return build_scan(
        "https://shop.test", "https://shop.test", headers, dom_scripts, network_scripts
    )


def test_external_script_is_hashed_and_keeps_its_integrity_attribute():
    scan = build_sample_scan()
    external = {script["url"]: script for script in scan["scripts"] if script["kind"] == "external"}

    assert external["https://a.com/x.js"]["sha256"] == hashlib.sha256(b"console.log(1)").hexdigest()
    assert external["https://a.com/x.js"]["integrity"] == "sha384-abc"


def test_script_loaded_by_the_network_but_absent_from_the_dom_is_kept():
    scan = build_sample_scan()
    external = {script["url"]: script for script in scan["scripts"] if script["kind"] == "external"}

    assert external["https://dynamic.net/d.js"]["in_dom"] is False
    assert external["https://dynamic.net/d.js"]["indicators"] == ["eval"]


def test_inline_script_is_hashed_and_data_blocks_are_ignored():
    scan = build_sample_scan()
    inline = [script for script in scan["scripts"] if script["kind"] == "inline"]

    assert len(inline) == 1
    assert inline[0]["sha256"] == hashlib.sha256(b"var a = 1;").hexdigest()


def test_only_tracked_security_headers_are_kept():
    assert build_sample_scan()["headers"] == {"x-frame-options": "DENY"}
