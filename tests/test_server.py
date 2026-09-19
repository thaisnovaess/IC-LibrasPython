from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from webapp.server import build_server


class ServerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        database_path = Path(self.temporary_directory.name) / "http.sqlite"
        self.server = build_server("127.0.0.1", 0, database_path)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.base_url = f"http://{host}:{port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temporary_directory.cleanup()

    def request(self, path: str, method: str = "GET", payload: dict | None = None):
        data = json.dumps(payload).encode() if payload is not None else None
        request = Request(
            self.base_url + path,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=2) as response:
            return response.status, json.load(response)

    def test_serves_page_and_complete_api_flow(self) -> None:
        with urlopen(self.base_url + "/", timeout=2) as response:
            page = response.read().decode()
        self.assertIn("Libras em texto", page)

        status, created = self.request("/api/sessions", "POST")
        self.assertEqual(201, status)

        event_status, _ = self.request(
            "/api/events",
            "POST",
            {
                "session_id": created["session_id"],
                "event_type": "letter",
                "confirmed_letter": "A",
                "source": "manual",
            },
        )
        self.assertEqual(201, event_status)

        _, session = self.request(f"/api/sessions/{created['session_id']}")
        self.assertEqual("A", session["text"])

    def test_prediction_endpoint_is_explicitly_unavailable(self) -> None:
        request = Request(self.base_url + "/api/predict", data=b"", method="POST")
        with self.assertRaises(HTTPError) as context:
            urlopen(request, timeout=2)
        error = context.exception
        try:
            self.assertEqual(503, error.code)
            payload = json.load(error)
            self.assertEqual("model_unavailable", payload["status"])
        finally:
            error.close()

    def test_prediction_rejects_invalid_frame_contract(self) -> None:
        request = Request(
            self.base_url + "/api/predict",
            data=json.dumps({"frames": []}).encode(),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with self.assertRaises(HTTPError) as context:
            urlopen(request, timeout=2)
        error = context.exception
        try:
            self.assertEqual(400, error.code)
            self.assertIn("entre 1 e 30", json.load(error)["error"])
        finally:
            error.close()
