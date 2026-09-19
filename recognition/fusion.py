"""Fusão conservadora das previsões manual e facial."""

from recognition.contracts import IntegratedPrediction, ModalityPrediction


def fuse_predictions(
    manual: ModalityPrediction,
    facial: ModalityPrediction,
) -> IntegratedPrediction:
    if not manual.available and not facial.available:
        return IntegratedPrediction(
            status="model_unavailable",
            manual_label=None,
            manual_confidence=None,
            manual_model_version=None,
            facial_expression=None,
            facial_confidence=None,
            facial_model_version=None,
            message="Os modelos manual e facial ainda não estão disponíveis.",
        )

    manual_valid = manual.available and manual.detected and manual.label is not None
    facial_valid = facial.available and facial.detected and facial.label is not None

    if not manual_valid and not facial_valid:
        status = "no_detection" if manual.available or facial.available else "model_unavailable"
        message = "Nenhuma mão ou expressão facial válida foi detectada."
    elif manual_valid and facial_valid:
        status = "ok"
        message = "Sinal manual e expressão facial identificados."
    else:
        status = "partial"
        missing = "expressão facial" if manual_valid else "sinal manual"
        message = f"Resultado parcial: {missing} não identificado."

    return IntegratedPrediction(
        status=status,
        manual_label=manual.label if manual_valid else None,
        manual_confidence=manual.confidence if manual_valid else None,
        manual_model_version=manual.model_version if manual.available else None,
        facial_expression=facial.label if facial_valid else None,
        facial_confidence=facial.confidence if facial_valid else None,
        facial_model_version=facial.model_version if facial.available else None,
        message=message,
    )
