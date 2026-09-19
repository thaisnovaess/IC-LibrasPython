"""Contrato persistente das amostras sincronizadas de mãos e face."""

from __future__ import annotations

import gzip
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4


HAND_POINTS = 21
FACE_POINTS = 468


@dataclass(frozen=True)
class SampleMetadata:
    participant_id: str
    manual_label: str
    facial_label: str
    lighting: str
    width: int
    height: int
    fps: float
    duration_seconds: float
    store_video: bool = False

    def validate(self) -> None:
        text_fields = {
            "participant_id": self.participant_id,
            "manual_label": self.manual_label,
            "facial_label": self.facial_label,
            "lighting": self.lighting,
        }
        missing = [name for name, value in text_fields.items() if not value.strip()]
        if missing:
            raise ValueError(f"Metadados obrigatórios ausentes: {', '.join(missing)}.")
        if self.width < 720 or self.height < 480:
            raise ValueError("A resolução mínima da coleta é 720x480.")
        if self.fps <= 0 or self.duration_seconds <= 0:
            raise ValueError("FPS e duração devem ser positivos.")


def _validate_points(points: Any, expected: int, field: str) -> None:
    if points is None:
        return
    if not isinstance(points, list) or len(points) != expected:
        raise ValueError(f"{field} deve conter {expected} landmarks.")
    if any(not isinstance(point, list) or len(point) != 3 for point in points):
        raise ValueError(f"Cada landmark de {field} deve conter x, y e z.")


def validate_frames(frames: list[dict[str, Any]]) -> None:
    if not frames:
        raise ValueError("A amostra deve conter ao menos um frame.")
    previous_timestamp = -1
    for frame in frames:
        timestamp = frame.get("timestamp_ms")
        if not isinstance(timestamp, int) or timestamp <= previous_timestamp:
            raise ValueError("Os timestamps devem ser inteiros e estritamente crescentes.")
        previous_timestamp = timestamp
        _validate_points(frame.get("left_hand"), HAND_POINTS, "left_hand")
        _validate_points(frame.get("right_hand"), HAND_POINTS, "right_hand")
        _validate_points(frame.get("face"), FACE_POINTS, "face")


def save_sample(
    output_directory: str | Path,
    metadata: SampleMetadata,
    frames: list[dict[str, Any]],
) -> Path:
    metadata.validate()
    validate_frames(frames)
    target_directory = Path(output_directory)
    target_directory.mkdir(parents=True, exist_ok=True)
    target = target_directory / f"sample-{uuid4()}.json.gz"
    payload = {"schema_version": 1, "metadata": asdict(metadata), "frames": frames}
    with gzip.open(target, "wt", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, separators=(",", ":"))
    return target


def load_sample(path: str | Path) -> dict[str, Any]:
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        payload = json.load(stream)
    if payload.get("schema_version") != 1:
        raise ValueError("Versão de amostra incompatível.")
    metadata = SampleMetadata(**payload["metadata"])
    metadata.validate()
    validate_frames(payload["frames"])
    return payload
