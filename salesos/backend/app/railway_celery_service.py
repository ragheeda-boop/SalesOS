import argparse
import os
import signal
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802 - stdlib handler method name
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"ok")
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        return


def _start_health_server(port: int) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("0.0.0.0", port), _HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def _build_command(role: str) -> list[str]:
    base = ["celery", "-A", "app.celery_app"]
    if role == "worker":
        return base + ["worker", "--loglevel=info", "--concurrency=2", "--max-tasks-per-child=1000"]
    if role == "beat":
        return base + ["beat", "--loglevel=info"]
    raise ValueError(f"Unsupported role: {role}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Celery with a lightweight Railway health server.")
    parser.add_argument("role", choices=("worker", "beat"))
    args = parser.parse_args()

    port = int(os.environ.get("PORT", "8080"))
    server = _start_health_server(port)
    child = subprocess.Popen(_build_command(args.role))

    def _shutdown(signum: int, _frame: object) -> None:
        if child.poll() is None:
            child.send_signal(signum)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    try:
        return child.wait()
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    sys.exit(main())
