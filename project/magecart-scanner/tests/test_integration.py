import importlib.util
import urllib.request
from pathlib import Path

import pytest

from magecart_scanner.compare import compare_scans
from magecart_scanner.inventory import scan_page

pytestmark = pytest.mark.browser

SERVE_MODULE_PATH = Path(__file__).parent.parent / "testbench" / "serve.py"
SHOP_URL = "http://localhost:8000/"
ANALYTICS_URL = "http://localhost:8001/analytics.js"
SHOP_SCRIPT_URL = "http://localhost:8000/static/shop.js"
SWITCH_TO_V2_URL = "http://localhost:8001/__variant/v2"


def load_serve_module():
    spec = importlib.util.spec_from_file_location("serve", SERVE_MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def running_testbench():
    serve = load_serve_module()
    try:
        servers = serve.start_servers()
    except OSError:
        pytest.skip("ports 8000 and 8001 are already in use")
    yield
    for server in servers:
        server.shutdown()


def scan_or_skip(url):
    try:
        return scan_page(url)
    except Exception as error:
        pytest.skip(f"Chromium is not available: {error}")


def test_scan_lists_the_scripts_of_the_test_page(running_testbench):
    scan = scan_or_skip(SHOP_URL)

    external_urls = {script["url"] for script in scan["scripts"] if script["kind"] == "external"}
    inline_count = sum(1 for script in scan["scripts"] if script["kind"] == "inline")
    assert external_urls == {SHOP_SCRIPT_URL, ANALYTICS_URL}
    assert inline_count == 1


def test_scan_detects_a_third_party_script_change(running_testbench):
    first_scan = scan_or_skip(SHOP_URL)
    urllib.request.urlopen(SWITCH_TO_V2_URL).read()
    second_scan = scan_page(SHOP_URL)

    diff = compare_scans(first_scan, second_scan)

    assert [change.url for change in diff.changed_scripts] == [ANALYTICS_URL]
    assert diff.added_scripts == []
    assert diff.removed_scripts == []
