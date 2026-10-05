from __future__ import annotations

import argparse
import functools
import http.server
import socket
import socketserver
from pathlib import Path


class ReusableTcpServer(socketserver.TCPServer):
    allow_reuse_address = True


def find_available_port(start_port: int) -> int:
    for port in range(start_port, start_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError(f"No available port found from {start_port} to {start_port + 49}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the BLR O-RAN Digital Twin web app.")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--strict-port", action="store_true", help="Fail instead of picking another port.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent / "web"
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(root))
    port = args.port if args.strict_port else find_available_port(args.port)
    if port != args.port:
        print(f"Port {args.port} is busy. Using http://127.0.0.1:{port} instead.")
    with ReusableTcpServer(("127.0.0.1", port), handler) as server:
        print(f"Serving {root} at http://127.0.0.1:{port}")
        server.serve_forever()


if __name__ == "__main__":
    main()
