from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from database.communication import CommunicationRepository
from webapp.application import CommunicationApplication, ValidationError


class CommunicationApplicationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        database_path = Path(self.temporary_directory.name) / "test.sqlite"
        self.application = CommunicationApplication(CommunicationRepository(database_path))
        self.session_id = self.application.create_session()["session_id"]

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def add(self, event_type: str, **values: object) -> dict:
        return self.application.add_event(
            {"session_id": self.session_id, "event_type": event_type, **values}
        )

    def test_builds_message_from_persisted_events(self) -> None:
        self.add("letter", confirmed_letter="O")
        self.add("letter", confirmed_letter="I")
        self.add("space")
        self.add("letter", confirmed_letter="A")
        self.add("backspace")

        session = self.application.session(self.session_id)

        self.assertEqual("OI ", session["text"])
        self.assertEqual(5, len(session["events"]))

    def test_records_correction_without_losing_prediction(self) -> None:
        event = self.add(
            "letter",
            confirmed_letter="B",
            predicted_letter="D",
            confidence=0.72,
            source="recognizer",
            model_version="test-v1",
        )

        self.assertEqual("D", event["predicted_letter"])
        self.assertEqual("B", event["confirmed_letter"])
        self.assertTrue(event["corrected"])

    def test_rejects_invalid_letter(self) -> None:
        with self.assertRaisesRegex(ValidationError, "exatamente uma letra"):
            self.add("letter", confirmed_letter="AB")

    def test_rejects_confidence_outside_range(self) -> None:
        with self.assertRaisesRegex(ValidationError, "entre 0 e 1"):
            self.add(
                "letter",
                confirmed_letter="A",
                predicted_letter="A",
                confidence=1.4,
                source="recognizer",
            )

    def test_reports_recognizer_as_unavailable(self) -> None:
        status = self.application.status()
        response_status, prediction = self.application.predict()

        self.assertFalse(status["recognizer"]["available"])
        self.assertEqual(503, response_status)
        self.assertEqual("model_unavailable", prediction["status"])

    def test_persists_facial_context_with_manual_prediction(self) -> None:
        event = self.application.add_event(
            {
                "session_id": self.session_id,
                "event_type": "letter",
                "confirmed_letter": "A",
                "predicted_letter": "A",
                "confidence": 0.91,
                "source": "recognizer",
                "model_version": "manual-v1",
                "facial_expression": "interrogativa",
                "facial_confidence": 0.82,
                "facial_model_version": "facial-v1",
            }
        )

        self.assertEqual("interrogativa", event["facial_expression"])
        self.assertEqual(0.82, event["facial_confidence"])

    def test_rejects_invalid_facial_confidence(self) -> None:
        with self.assertRaisesRegex(ValidationError, "confiança facial"):
            self.application.add_event(
                {
                    "session_id": self.session_id,
                    "event_type": "letter",
                    "confirmed_letter": "A",
                    "source": "manual",
                    "facial_confidence": 2,
                }
            )
