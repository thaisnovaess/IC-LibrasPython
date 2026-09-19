"""Contratos independentes de bibliotecas de visão e aprendizado de máquina."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModalityPrediction:
    label: str | None
    confidence: float | None
    model_version: str | None
    detected: bool
    available: bool = True

    def __post_init__(self) -> None:
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("A confiança deve estar entre 0 e 1.")
        if self.label is not None and not self.detected:
            raise ValueError("Um rótulo exige uma detecção válida.")


@dataclass(frozen=True)
class IntegratedPrediction:
    status: str
    manual_label: str | None
    manual_confidence: float | None
    manual_model_version: str | None
    facial_expression: str | None
    facial_confidence: float | None
    facial_model_version: str | None
    message: str

    @property
    def predicted_letter(self) -> str | None:
        """Compatibilidade temporária com o MVP de datilologia."""
        if self.manual_label and len(self.manual_label) == 1:
            return self.manual_label
        return None

    @property
    def confidence(self) -> float | None:
        return self.manual_confidence

    @property
    def model_version(self) -> str | None:
        return self.manual_model_version
