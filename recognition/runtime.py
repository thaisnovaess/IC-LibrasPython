"""Runtime local para landmarks, modelos e fusão de previsões."""

from __future__ import annotations

from pathlib import Path
from threading import Lock

from recognition.contracts import IntegratedPrediction, ModalityPrediction
from recognition.features import modality_features, static_manual_features
from recognition.fusion import fuse_predictions


def _landmarks(value) -> list[list[float]] | None:
    if value is None:
        return None
    return [[point.x, point.y, point.z] for point in value.landmark]


def _manual_features_for_artifact(artifact: dict, frames: list[dict]) -> list[float]:
    contract = artifact.get("feature_contract", "manual-temporal-v1")
    if contract == "manual-static-v1":
        return static_manual_features(frames)
    if contract == "manual-temporal-v1":
        return modality_features(frames, "manual")
    raise ValueError(f"Contrato de features manual desconhecido: {contract}.")


def _validate_manual_artifact(artifact: dict) -> None:
    contract = artifact.get("feature_contract", "manual-temporal-v1")
    if contract not in {"manual-static-v1", "manual-temporal-v1"}:
        raise ValueError(f"Contrato de features manual desconhecido: {contract}.")


class IntegratedRecognizer:
    def __init__(self, models_directory: str | Path = "artifacts/models") -> None:
        self.models_directory = Path(models_directory)
        self._error: str | None = None
        self._manual_artifact = None
        self._facial_artifact = None
        self._hands = None
        self._holistic = None
        self._vision_lock = Lock()
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
                try:
                    _validate_manual_artifact(self._manual_artifact)
                except ValueError as exc:
                    self._error = str(exc)
                    self._manual_artifact = None
            if facial_path.exists():
                self._facial_artifact = joblib.load(facial_path)
            manual_contract = (
                self._manual_artifact.get("feature_contract", "manual-temporal-v1")
                if self._manual_artifact
                else None
            )
            if manual_contract == "manual-static-v1":
                self._hands = mp.solutions.hands.Hands(
                    static_image_mode=True,
                    max_num_hands=2,
                    model_complexity=1,
                    min_detection_confidence=0.3,
                    min_tracking_confidence=0.5,
                )
            if manual_contract == "manual-temporal-v1" or self._facial_artifact:
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
        if self._manual_artifact is None:
            return False
        contract = self._manual_artifact.get("feature_contract", "manual-temporal-v1")
        if contract == "manual-static-v1":
            return self._hands is not None
        return self._holistic is not None

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

    def _decode_image(self, encoded: bytes):
        image = self.cv2.imdecode(
            self.np.frombuffer(encoded, dtype=self.np.uint8),
            self.cv2.IMREAD_COLOR,
        )
        if image is None:
            raise ValueError("Uma das imagens da sequência é inválida.")
        return image

    def _detect_hands(self, rgb_image) -> list[list[list[float]]]:
        if self._hands is None:
            return []
        with self._vision_lock:
            result = self._hands.process(rgb_image)
        return [_landmarks(hand) for hand in (result.multi_hand_landmarks or [])]

    def detect_hands(self, encoded_image: bytes) -> list[list[list[float]]]:
        """Retorna landmarks normalizados para a sobreposição local da câmera."""
        image = self._decode_image(encoded_image)
        rgb_image = self.cv2.cvtColor(image, self.cv2.COLOR_BGR2RGB)
        return self._detect_hands(rgb_image)

    def inspect_frame(self, encoded_image: bytes) -> dict:
        """Detecta a mão uma vez e produz landmarks e prévia estática."""
        hands = self.detect_hands(encoded_image)
        preview = None
        contract = (
            self._manual_artifact.get("feature_contract", "manual-temporal-v1")
            if self._manual_artifact
            else None
        )
        if hands and contract == "manual-static-v1":
            prediction = self._predict(
                self._manual_artifact,
                static_manual_features([{"left_hand": None, "right_hand": hands[0]}]),
            )
            preview = {
                "letter": prediction.label,
                "confidence": prediction.confidence,
                "model_version": prediction.model_version,
            }
        return {"hands": hands, "preview": preview}

    def recognize_sequence(self, encoded_frames: list[bytes]) -> IntegratedPrediction:
        if not self.available:
            unavailable = ModalityPrediction(None, None, None, detected=False, available=False)
            return fuse_predictions(unavailable, unavailable)
        if not encoded_frames:
            raise ValueError("A sequência de imagens não pode ser vazia.")

        frames: list[dict] = []
        for index, encoded in enumerate(encoded_frames):
            image = self._decode_image(encoded)
            rgb_image = self.cv2.cvtColor(image, self.cv2.COLOR_BGR2RGB)
            left_hand = None
            right_hand = None
            face = None
            if self._hands is not None:
                detected_hands = self._detect_hands(rgb_image)
                if detected_hands:
                    right_hand = detected_hands[0]
                if len(detected_hands) > 1:
                    left_hand = detected_hands[1]
            if self._holistic is not None:
                with self._vision_lock:
                    holistic_result = self._holistic.process(rgb_image)
                if self._hands is None:
                    left_hand = _landmarks(holistic_result.left_hand_landmarks)
                    right_hand = _landmarks(holistic_result.right_hand_landmarks)
                face = _landmarks(holistic_result.face_landmarks)
            frames.append(
                {
                    "timestamp_ms": index + 1,
                    "left_hand": left_hand,
                    "right_hand": right_hand,
                    "face": face,
                }
            )

        hand_detected = any(frame["left_hand"] or frame["right_hand"] for frame in frames)
        face_detected = any(frame["face"] for frame in frames)
        manual = (
            self._predict(
                self._manual_artifact,
                _manual_features_for_artifact(self._manual_artifact, frames),
            )
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
        if self._hands is not None:
            self._hands.close()
        if self._holistic is not None:
            self._holistic.close()
