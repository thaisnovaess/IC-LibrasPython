from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import joblib

from recognition.contracts import ModalityPrediction
from recognition.fusion import fuse_predictions
from recognition.runtime import IntegratedRecognizer, _manual_features_for_artifact


def landmarks(count: int) -> list[list[float]]:
    return [[index * 0.01, (index % 7) * 0.02, index * 0.001] for index in range(count)]


class FusionTest(unittest.TestCase):
    def test_combines_manual_and_facial_predictions(self) -> None:
        result = fuse_predictions(
            ModalityPrediction("A", 0.91, "manual-v1", detected=True),
            ModalityPrediction("interrogativa", 0.84, "facial-v1", detected=True),
        )

        self.assertEqual("ok", result.status)
        self.assertEqual("A", result.manual_label)
        self.assertEqual("interrogativa", result.facial_expression)
        self.assertEqual(0.91, result.manual_confidence)
        self.assertEqual(0.84, result.facial_confidence)

    def test_returns_partial_when_face_is_not_detected(self) -> None:
        result = fuse_predictions(
            ModalityPrediction("B", 0.8, "manual-v1", detected=True),
            ModalityPrediction(None, None, "facial-v1", detected=False),
        )

        self.assertEqual("partial", result.status)
        self.assertEqual("B", result.manual_label)
        self.assertIsNone(result.facial_expression)

    def test_returns_no_detection_without_labels(self) -> None:
        result = fuse_predictions(
            ModalityPrediction(None, None, "manual-v1", detected=False),
            ModalityPrediction(None, None, "facial-v1", detected=False),
        )

        self.assertEqual("no_detection", result.status)

    def test_returns_model_unavailable_without_models(self) -> None:
        result = fuse_predictions(
            ModalityPrediction(None, None, None, detected=False, available=False),
            ModalityPrediction(None, None, None, detected=False, available=False),
        )

        self.assertEqual("model_unavailable", result.status)
        self.assertIsNone(result.manual_label)

    def test_rejects_confidence_outside_probability_range(self) -> None:
        with self.assertRaisesRegex(ValueError, "entre 0 e 1"):
            ModalityPrediction("A", 1.1, "manual-v1", detected=True)


class RuntimeFeatureContractTest(unittest.TestCase):
    def test_static_artifact_uses_63_manual_features(self) -> None:
        result = _manual_features_for_artifact(
            {"feature_contract": "manual-static-v1"},
            [{"left_hand": landmarks(21), "right_hand": None}],
        )

        self.assertEqual(63, len(result))

    def test_static_artifact_initializes_hands_detector_and_is_available(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            joblib.dump(
                {
                    "model": None,
                    "model_version": "static-v1",
                    "feature_contract": "manual-static-v1",
                },
                Path(directory) / "manual.joblib",
            )
            recognizer = IntegratedRecognizer(directory)
            try:
                readiness = recognizer.readiness()
                uses_hands = recognizer._hands is not None
                uses_holistic = recognizer._holistic is not None
            finally:
                recognizer.close()

        self.assertTrue(readiness["available"])
        self.assertTrue(readiness["manual_available"])
        self.assertTrue(uses_hands)
        self.assertFalse(uses_holistic)

    def test_unknown_contract_makes_runtime_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            joblib.dump(
                {
                    "model": None,
                    "model_version": "invalid-v1",
                    "feature_contract": "unknown-v9",
                },
                Path(directory) / "manual.joblib",
            )
            recognizer = IntegratedRecognizer(directory)
            try:
                readiness = recognizer.readiness()
            finally:
                recognizer.close()

        self.assertFalse(readiness["available"])
        self.assertFalse(readiness["manual_available"])
        self.assertIn("Contrato de features manual desconhecido", readiness["message"])
