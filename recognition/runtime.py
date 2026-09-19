"""Runtime local para landmarks, modelos e fusão de previsões."""

from __future__ import annotations

from pathlib import Path

from recognition.contracts import IntegratedPrediction, ModalityPrediction
from recognition.features import modality_features
from recognition.fusion import fuse_predictions


def _landmarks(value) -> list[list[float]] | None:
    if value is None:
        return None
    return [[point.x, point.y, point.z] for point in value.landmark]


class IntegratedRecognizer:
    def __init__(self, models_directory: str | Path = "artifacts/models") -> None:
        self.models_directory = Path(models_directory)
        self._error: str | None = None
        self._manual_artifact = None
        self._facial_artifact = None
        self._holistic = None
        try:
            import cv2
            import joblib
            import mediapipe as mp
            import numpy as np

            self.cv2 = cv2
            self.np = np
            manual_path = self.models_directory / "manual.joblib"
            facial_path = self.models_directory / "facial.joblib"
            if manual_path.exists():
                self._manual_artifact = joblib.load(manual_path)
            if facial_path.exists():
                self._facial_artifact = joblib.load(facial_path)
            self._holistic = mp.solutions.holistic.Holistic(
                static_image_mode=False,
                model_complexity=1,
                refine_face_landmarks=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
        except ImportError:
            self._error = "Instale requirements-vision.txt em um ambiente Python 3.11."
        except Exception as exc:
            self._error = f"Falha ao carregar o runtime local: {exc}"

    @property
    def available(self) -> bool:
        return self._holistic is not None and self._manual_artifact is not None

    @property
    def model_version(self) -> str | None:
        if self._manual_artifact:
            return self._manual_artifact.get("model_version")
        return None

    def readiness(self) -> dict:
        return {
            "available": self.available,
            "manual_available": self._manual_artifact is not None,
            "facial_available": self._facial_artifact is not None,
            "manual_model_version": self.model_version,
            "facial_model_version": (
                self._facial_artifact.get("model_version") if self._facial_artifact else None
            ),
            "message": self._error or (
                "Reconhecimento manual pronto."
                if self.available
                else "Modelo manual ainda não treinado. Execute o coletor e o treinamento."
            ),
        }

    def _predict(self, artifact, features: list[float]) -> ModalityPrediction:
        if artifact is None:
            return ModalityPrediction(None, None, None, detected=False, available=False)
        model = artifact["model"]
        probabilities = model.predict_proba([features])[0]
        best_index = int(self.np.argmax(probabilities))
        return ModalityPrediction(
            label=str(model.classes_[best_index]),
            confidence=float(probabilities[best_index]),
            model_version=artifact["model_version"],
            detected=True,
        )

    def recognize_sequence(self, encoded_frames: list[bytes]) -> IntegratedPrediction:
        if not self.available:
            unavailable = ModalityPrediction(None, None, None, detected=False, available=False)
            return fuse_predictions(unavailable, unavailable)
        if not encoded_frames:
            raise ValueError("A sequência de imagens não pode ser vazia.")

        frames: list[dict] = []
        for index, encoded in enumerate(encoded_frames):
            image = self.cv2.imdecode(self.np.frombuffer(encoded, dtype=self.np.uint8), self.cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError("Uma das imagens da sequência é inválida.")
            result = self._holistic.process(self.cv2.cvtColor(image, self.cv2.COLOR_BGR2RGB))
            frames.append(
                {
                    "timestamp_ms": index + 1,
                    "left_hand": _landmarks(result.left_hand_landmarks),
                    "right_hand": _landmarks(result.right_hand_landmarks),
                    "face": _landmarks(result.face_landmarks),
                }
            )

        hand_detected = any(frame["left_hand"] or frame["right_hand"] for frame in frames)
        face_detected = any(frame["face"] for frame in frames)
        manual = (
            self._predict(self._manual_artifact, modality_features(frames, "manual"))
            if hand_detected
            else ModalityPrediction(None, None, self.model_version, detected=False)
        )
        facial = (
            self._predict(self._facial_artifact, modality_features(frames, "facial"))
            if face_detected and self._facial_artifact
            else ModalityPrediction(
                None,
                None,
                self._facial_artifact.get("model_version") if self._facial_artifact else None,
                detected=False,
                available=self._facial_artifact is not None,
            )
        )
        return fuse_predictions(manual, facial)

    def close(self) -> None:
        if self._holistic is not None:
            self._holistic.close()
