"""Casos de uso e validação da interface web."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from database.communication import CommunicationRepository
from models.recognizer import UnavailableRecognizer


class ValidationError(ValueError):
    pass


def _letter(value: Any, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str):
        raise ValidationError("A letra deve ser um texto entre A e Z.")
    normalized = value.strip().upper()
    if len(normalized) != 1 or normalized < "A" or normalized > "Z":
        raise ValidationError("Informe exatamente uma letra entre A e Z.")
    return normalized


class CommunicationApplication:
    def __init__(
        self,
        repository: CommunicationRepository,
        recognizer: UnavailableRecognizer | None = None,
    ) -> None:
        self.repository = repository
        self.recognizer = recognizer or UnavailableRecognizer()

    def status(self) -> dict[str, Any]:
        readiness = self.recognizer.readiness()
        return {
            "service": "ready",
            "recognizer": {
                **readiness,
                "status": "ready" if readiness["available"] else "model_unavailable",
                "model_version": readiness["manual_model_version"],
            },
        }

    def create_session(self) -> dict[str, str]:
        return {"session_id": self.repository.create_session()}

    def session(self, session_id: str) -> dict[str, Any]:
        if not self.repository.session_exists(session_id):
            raise LookupError("Sessão não encontrada.")
        events = [asdict(event) for event in self.repository.list_events(session_id)]
        text = ""
        for event in events:
            if event["event_type"] == "letter":
                text += event["confirmed_letter"]
            elif event["event_type"] == "space" and text and not text.endswith(" "):
                text += " "
            elif event["event_type"] == "backspace":
                text = text[:-1]
            elif event["event_type"] == "clear":
                text = ""
        return {
            "session_id": session_id,
            "events": events,
            "text": text,
        }

    def add_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        session_id = payload.get("session_id")
        if not isinstance(session_id, str) or not self.repository.session_exists(session_id):
            raise LookupError("Sessão não encontrada.")

        event_type = payload.get("event_type", "letter")
        if event_type not in {"letter", "space", "backspace", "clear"}:
            raise ValidationError("Tipo de evento inválido.")

        confirmed = _letter(payload.get("confirmed_letter")) if event_type == "letter" else None
        predicted = (
            _letter(payload.get("predicted_letter"), optional=True)
            if event_type == "letter"
            else None
        )

        confidence = payload.get("confidence")
        if confidence is not None:
            if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
                raise ValidationError("A confiança deve ser um número entre 0 e 1.")
            confidence = float(confidence)
            if confidence < 0 or confidence > 1:
                raise ValidationError("A confiança deve ser um número entre 0 e 1.")

        facial_confidence = payload.get("facial_confidence")
        if facial_confidence is not None:
            if isinstance(facial_confidence, bool) or not isinstance(facial_confidence, (int, float)):
                raise ValidationError("A confiança facial deve ser um número entre 0 e 1.")
            facial_confidence = float(facial_confidence)
            if not 0 <= facial_confidence <= 1:
                raise ValidationError("A confiança facial deve ser um número entre 0 e 1.")

        source = payload.get("source", "manual")
        if source not in {"manual", "recognizer"}:
            raise ValidationError("A origem deve ser manual ou recognizer.")
        if source == "manual" and predicted is not None:
            raise ValidationError("Uma inserção manual não pode ter letra prevista.")
        if source == "recognizer" and predicted is None:
            raise ValidationError("Uma previsão precisa informar a letra identificada.")

        event = self.repository.add_event(
            session_id=session_id,
            event_type=event_type,
            confirmed_letter=confirmed,
            predicted_letter=predicted,
            confidence=confidence,
            source=source,
            model_version=payload.get("model_version"),
            facial_expression=payload.get("facial_expression"),
            facial_confidence=facial_confidence,
            facial_model_version=payload.get("facial_model_version"),
        )
        return asdict(event)

    def predict(self, frames: list[bytes] | None = None) -> tuple[int, dict[str, Any]]:
        result = self.recognizer.recognize_sequence(frames or [])
        return (503 if result.status == "model_unavailable" else 200, asdict(result))
