import threading
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

TESTBENCH_ROOT = Path(__file__).parent
LOCAL_ADDRESS = "127.0.0.1"
SHOP_PORT = 8000
THIRD_PARTY_PORT = 8001
AVAILABLE_VARIANTS = ("v1", "v2")
DEFAULT_VARIANT = "v1"
VARIANT_ROUTE_PREFIX = "/__variant/"
ANALYTICS_ROUTE = "/analytics.js"

third_party_state = {"variant": DEFAULT_VARIANT}


class ShopRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(TESTBENCH_ROOT / "shop"), **kwargs)

    def log_message(self, *args):
        pass


class ThirdPartyRequestHandler(BaseHTTPRequestHandler):
    def send_text(self, status_code: int, body: str, content_type: str) -> None:
        payload = body.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def switch_variant(self, variant: str) -> None:
        if variant in AVAILABLE_VARIANTS:
            third_party_state["variant"] = variant
            self.send_text(200, f"variant={variant}\n", "text/plain")
        else:
            self.send_text(404, "unknown variant\n", "text/plain")

    def serve_analytics_script(self) -> None:
        script_path = (
            TESTBENCH_ROOT / "third_party" / f"analytics_{third_party_state['variant']}.js"
        )
        self.send_text(200, script_path.read_text(encoding="utf-8"), "application/javascript")

    def do_GET(self):
        route = self.path.split("?")[0]
        if route.startswith(VARIANT_ROUTE_PREFIX):
            self.switch_variant(route.removeprefix(VARIANT_ROUTE_PREFIX))
        elif route == ANALYTICS_ROUTE:
            self.serve_analytics_script()
        else:
            self.send_text(404, "not found\n", "text/plain")

    def log_message(self, *args):
        pass


def start_servers(shop_port: int = SHOP_PORT, third_party_port: int = THIRD_PARTY_PORT):
    third_party_state["variant"] = DEFAULT_VARIANT
    servers = [
        ThreadingHTTPServer((LOCAL_ADDRESS, shop_port), ShopRequestHandler),
        ThreadingHTTPServer((LOCAL_ADDRESS, third_party_port), ThirdPartyRequestHandler),
    ]
    for server in servers:
        threading.Thread(target=server.serve_forever, daemon=True).start()
    return servers


def main() -> None:
    servers = start_servers()
    print(f"Shop:        http://localhost:{SHOP_PORT}/")
    print(f"Third party: http://localhost:{THIRD_PARTY_PORT}{ANALYTICS_ROUTE} (v1)")
    switch_url = f"http://localhost:{THIRD_PARTY_PORT}{VARIANT_ROUTE_PREFIX}v2"
    print(f"Switch the third-party script: {switch_url} (or v1)")
    print("Press Ctrl+C to stop.")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        for server in servers:
            server.shutdown()


if __name__ == "__main__":
    main()
