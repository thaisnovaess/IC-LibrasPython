"""Adaptadores do reconhecedor local integrado."""

from __future__ import annotations

from recognition.contracts import IntegratedPrediction
from recognition.runtime import IntegratedRecognizer


class UnavailableRecognizer:
    """Estado honesto até existir um artefato de modelo validado."""

    available = False
    model_version = None

    def readiness(self) -> dict:
        return {
            "available": False,
            "manual_available": False,
            "facial_available": False,
            "manual_model_version": None,
            "facial_model_version": None,
            "message": "O modelo manual ainda não foi treinado.",
        }

    def recognize_sequence(self, _images: list[bytes] | None = None) -> IntegratedPrediction:
        return IntegratedPrediction(
            status="model_unavailable",
            manual_label=None,
            manual_confidence=None,
            manual_model_version=None,
            facial_expression=None,
            facial_confidence=None,
            facial_model_version=None,
            message=(
                "O modelo manual ainda não foi treinado. "
                "Use a inserção manual durante esta etapa do MVP."
            ),
        )

    def detect_hands(self, _image: bytes) -> list:
        return []

    def inspect_frame(self, _image: bytes) -> dict:
        return {"hands": [], "preview": None}

    def recognize(self, _image: bytes | None = None) -> IntegratedPrediction:
        return self.recognize_sequence([])


def build_recognizer(models_directory: str = "artifacts/models"):
    recognizer = IntegratedRecognizer(models_directory)
    return recognizer if recognizer.available else recognizer
