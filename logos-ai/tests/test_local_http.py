import json, threading, unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
from logos_ai.inference import Client, Unavailable
from logos_ai.config import DEFAULTS


class LocalHTTP(unittest.TestCase):
    def test_schema_sent_and_only_loopback_used_despite_proxy(self):
        received = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                received.append(data)
                body = json.dumps(
                    {
                        "choices": [
                            {
                                "message": {
                                    "content": json.dumps(
                                        {
                                            "message": "GPU status",
                                            "commands": [
                                                {
                                                    "command": "nvidia-smi",
                                                    "description": "GPU status",
                                                    "risk": "low",
                                                }
                                            ],
                                        }
                                    )
                                }
                            }
                        ]
                    }
                ).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with patch.dict(
                "os.environ",
                {
                    "http_proxy": "http://127.0.0.1:1",
                    "HTTP_PROXY": "http://127.0.0.1:1",
                    "NO_PROXY": "",
                },
            ):
                result = Client(
                    {**DEFAULTS, "LLAMA_PORT": str(server.server_port)}
                ).ask("show gpu", {"username": "logos"})
            self.assertEqual(result["commands"][0]["command"], "nvidia-smi")
            self.assertEqual(received[0]["response_format"]["type"], "json_object")
            self.assertIn("schema", received[0]["response_format"])
            self.assertNotIn("tools", received[0])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_redirect_rejected_before_any_remote_connection(self):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                self.send_response(302)
                self.send_header("Location", "https://example.invalid/")
                self.end_headers()

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with self.assertRaises(Unavailable):
                Client({**DEFAULTS, "LLAMA_PORT": str(server.server_port)}).request(
                    "/health"
                )
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
