from __future__ import annotations

import unittest

from recognition.contracts import ModalityPrediction
from recognition.fusion import fuse_predictions


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
