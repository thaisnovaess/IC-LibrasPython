from __future__ import annotations

import base64
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import joblib
import cv2
import numpy as np

from recognition.runtime import IntegratedRecognizer
from webapp.server import build_server


class FixedProbabilityModel:
    classes_ = ["A", "B"]

    def predict_proba(self, rows):
        return [[0.91, 0.09] for _ in rows]


class FakePoint:
    def __init__(self, index: int) -> None:
        self.x = index * 0.02
        self.y = (index % 5) * 0.03
        self.z = index * 0.001


class FakeHand:
    landmark = [FakePoint(index) for index in range(21)]


class FakeHands:
    def __init__(self, hands=None) -> None:
        self.hands = [FakeHand()] if hands is None else hands
        self.process_count = 0

    def process(self, _image):
        self.process_count += 1
        return type("HandsResult", (), {"multi_hand_landmarks": self.hands})()

    def close(self) -> None:
        pass


class ServerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        database_path = Path(self.temporary_directory.name) / "http.sqlite"
        models_directory = Path(self.temporary_directory.name) / "models"
        self.server = build_server("127.0.0.1", 0, database_path, models_directory)
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
        self.assertIn('id="hand-overlay"', page)
        self.assertIn('id="live-preview"', page)
        self.assertIn('id="signal-history"', page)
        self.assertIn('src="/hand-overlay.js"', page)
        self.assertIn('src="/session-history.js"', page)
        self.assertIn('maxlength="500"', page)

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

    def test_adds_complete_manual_phrase(self) -> None:
        _, created = self.request("/api/sessions", "POST")

        status, result = self.request(
            "/api/text",
            "POST",
            {"session_id": created["session_id"], "text": "Olá,   mundo!"},
        )
        _, session = self.request(f"/api/sessions/{created['session_id']}")

        self.assertEqual(201, status)
        self.assertEqual("Olá, mundo!", result["text"])
        self.assertEqual(11, result["added_characters"])
        self.assertEqual("Olá, mundo!", session["text"])

    def test_rejects_empty_manual_phrase(self) -> None:
        _, created = self.request("/api/sessions", "POST")
        invalid_texts = (
            ("  \n ", "Digite uma frase"),
            ("a" * 501, "no máximo 500"),
        )
        for text, expected_message in invalid_texts:
            with self.subTest(expected_message=expected_message):
                request = Request(
                    self.base_url + "/api/text",
                    data=json.dumps(
                        {"session_id": created["session_id"], "text": text}
                    ).encode(),
                    method="POST",
                    headers={"Content-Type": "application/json"},
                )
                with self.assertRaises(HTTPError) as context:
                    urlopen(request, timeout=2)
                error = context.exception
                try:
                    self.assertEqual(400, error.code)
                    self.assertIn(expected_message, json.load(error)["error"])
                finally:
                    error.close()

    def test_landmarks_reject_invalid_frame_contract(self) -> None:
        request = Request(
            self.base_url + "/api/landmarks",
            data=json.dumps({"frame": "invalid"}).encode(),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with self.assertRaises(HTTPError) as context:
            urlopen(request, timeout=2)
        error = context.exception
        try:
            self.assertEqual(400, error.code)
            self.assertIn("data URL inválido", json.load(error)["error"])
        finally:
            error.close()

    def test_status_reports_static_manual_model_as_available(self) -> None:
        models_directory = Path(self.temporary_directory.name) / "ready-models"
        models_directory.mkdir()
        joblib.dump(
            {
                "model": None,
                "model_version": "static-v1",
                "feature_contract": "manual-static-v1",
            },
            models_directory / "manual.joblib",
        )
        database_path = Path(self.temporary_directory.name) / "ready.sqlite"
        server = build_server("127.0.0.1", 0, database_path, models_directory)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host, port = server.server_address
        try:
            with urlopen(f"http://{host}:{port}/api/status", timeout=2) as response:
                payload = json.load(response)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
            server.RequestHandlerClass.application.recognizer.close()

        self.assertTrue(payload["recognizer"]["available"])
        self.assertTrue(payload["recognizer"]["manual_available"])

    def test_predicts_letter_through_http_with_static_artifact(self) -> None:
        models_directory = Path(self.temporary_directory.name) / "predict-models"
        models_directory.mkdir()
        joblib.dump(
            {
                "model": FixedProbabilityModel(),
                "model_version": "static-fixture-v1",
                "feature_contract": "manual-static-v1",
            },
            models_directory / "manual.joblib",
        )
        recognizer = IntegratedRecognizer(models_directory)
        recognizer._hands.close()
        detector = FakeHands()
        recognizer._hands = detector

        database_path = Path(self.temporary_directory.name) / "predict.sqlite"
        server = build_server(
            "127.0.0.1",
            0,
            database_path,
            models_directory,
            recognizer=recognizer,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host, port = server.server_address
        ok, encoded = cv2.imencode(".jpg", np.zeros((32, 32, 3), dtype=np.uint8))
        self.assertTrue(ok)
        data_url = "data:image/jpeg;base64," + base64.b64encode(encoded).decode()
        request = Request(
            f"http://{host}:{port}/api/predict",
            data=json.dumps({"frames": [data_url]}).encode(),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urlopen(request, timeout=2) as response:
                status = response.status
                payload = json.load(response)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
            recognizer.close()

        self.assertEqual(200, status)
        self.assertEqual("A", payload["manual_label"])
        self.assertEqual(0.91, payload["manual_confidence"])
        self.assertEqual("static-fixture-v1", payload["manual_model_version"])

    def test_returns_detected_hand_landmarks_for_camera_overlay(self) -> None:
        models_directory = Path(self.temporary_directory.name) / "overlay-models"
        models_directory.mkdir()
        joblib.dump(
            {
                "model": FixedProbabilityModel(),
                "model_version": "static-overlay-v1",
                "feature_contract": "manual-static-v1",
            },
            models_directory / "manual.joblib",
        )
        recognizer = IntegratedRecognizer(models_directory)
        recognizer._hands.close()
        detector = FakeHands()
        recognizer._hands = detector

        database_path = Path(self.temporary_directory.name) / "overlay.sqlite"
        server = build_server(
            "127.0.0.1",
            0,
            database_path,
            models_directory,
            recognizer=recognizer,
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host, port = server.server_address
        ok, encoded = cv2.imencode(".jpg", np.zeros((32, 32, 3), dtype=np.uint8))
        self.assertTrue(ok)
        data_url = "data:image/jpeg;base64," + base64.b64encode(encoded).decode()

        def request_landmarks() -> tuple[int, dict]:
            request = Request(
                f"http://{host}:{port}/api/landmarks",
                data=json.dumps({"frame": data_url}).encode(),
                method="POST",
                headers={"Content-Type": "application/json"},
            )
            with urlopen(request, timeout=2) as response:
                return response.status, json.load(response)

        try:
            detected_status, detected = request_landmarks()
            recognizer._hands = FakeHands([])
            empty_status, empty = request_landmarks()
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
            recognizer.close()

        self.assertEqual(200, detected_status)
        self.assertEqual(1, len(detected["hands"]))
        self.assertEqual(21, len(detected["hands"][0]))
        self.assertEqual([0.0, 0.0, 0.0], detected["hands"][0][0])
        self.assertEqual(1, detector.process_count)
        self.assertEqual("A", detected["preview"]["letter"])
        self.assertEqual(0.91, detected["preview"]["confidence"])
        self.assertEqual("static-overlay-v1", detected["preview"]["model_version"])
        self.assertEqual(200, empty_status)
        self.assertEqual([], empty["hands"])
        self.assertIsNone(empty["preview"])
