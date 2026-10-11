from magecart_scanner.compare import ScriptChange, compare_scans, format_diff


def make_scan(scripts, headers=None):
    return {"scanned_at": "2026-01-01T00:00:00+00:00", "scripts": scripts, "headers": headers or {}}


def make_external_script(url, sha256):
    return {"kind": "external", "url": url, "sha256": sha256}


def make_inline_script(sha256):
    return {"kind": "inline", "sha256": sha256}


def test_identical_scans_have_no_changes():
    scan = make_scan([make_external_script("https://a.com/x.js", "1"), make_inline_script("2")])

    assert compare_scans(scan, scan).has_changes is False


def test_detects_added_removed_and_changed_external_scripts():
    old_scan = make_scan(
        [
            make_external_script("https://a.com/x.js", "1"),
            make_external_script("https://a.com/gone.js", "9"),
        ]
    )
    new_scan = make_scan(
        [
            make_external_script("https://a.com/x.js", "2"),
            make_external_script("https://b.com/new.js", "3"),
        ]
    )

    diff = compare_scans(old_scan, new_scan)

    assert diff.added_scripts == ["https://b.com/new.js"]
    assert diff.removed_scripts == ["https://a.com/gone.js"]
    assert diff.changed_scripts == [ScriptChange("https://a.com/x.js", "1", "2")]
    assert diff.has_changes is True


def test_modified_inline_script_is_reported_as_removed_then_added():
    diff = compare_scans(
        make_scan([make_inline_script("aaa")]), make_scan([make_inline_script("bbb")])
    )

    assert diff.removed_inline_hashes == ["aaa"]
    assert diff.added_inline_hashes == ["bbb"]


def test_detects_added_removed_and_changed_headers():
    old_scan = make_scan(
        [], {"content-security-policy": "default-src 'self'", "x-frame-options": "DENY"}
    )
    new_scan = make_scan(
        [], {"content-security-policy": "default-src *", "referrer-policy": "no-referrer"}
    )

    diff = compare_scans(old_scan, new_scan)

    assert diff.added_headers == ["referrer-policy"]
    assert diff.removed_headers == ["x-frame-options"]
    assert [change.name for change in diff.changed_headers] == ["content-security-policy"]


def test_formatted_diff_mentions_changed_script():
    old_scan = make_scan([make_external_script("https://a.com/x.js", "1")])
    new_scan = make_scan([make_external_script("https://a.com/x.js", "2")])

    assert "Script CHANGED: https://a.com/x.js" in format_diff(
        compare_scans(old_scan, new_scan), old_scan, new_scan
    )


def test_formatted_diff_reports_no_changes_for_identical_scans():
    scan = make_scan([])

    assert "No changes detected." in format_diff(compare_scans(scan, scan), scan, scan)
