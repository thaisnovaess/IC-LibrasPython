"""Normalização geométrica e temporal compartilhada por treino e inferência."""

from __future__ import annotations

import math
from typing import Sequence

from recognition.dataset import FACE_POINTS, HAND_POINTS


Point = list[float]
Landmarks = list[Point]


def normalize_landmarks(
    points: Landmarks,
    *,
    expected_points: int,
    origin_index: int,
    scale_pair: tuple[int, int],
    alignment_pair: tuple[int, int],
) -> Landmarks:
    if len(points) != expected_points:
        raise ValueError(f"Esperados {expected_points} landmarks, recebidos {len(points)}.")
    origin = points[origin_index]
    translated = [[p[0] - origin[0], p[1] - origin[1], p[2] - origin[2]] for p in points]
    first, second = translated[scale_pair[0]], translated[scale_pair[1]]
    scale = math.dist(first, second)
    if scale <= 1e-9:
        raise ValueError("Não foi possível calcular a escala dos landmarks.")
    scaled = [[x / scale, y / scale, z / scale] for x, y, z in translated]
    start, end = scaled[alignment_pair[0]], scaled[alignment_pair[1]]
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    cosine, sine = math.cos(-angle), math.sin(-angle)
    return [
        [x * cosine - y * sine, x * sine + y * cosine, z]
        for x, y, z in scaled
    ]


def normalize_hand(points: Landmarks) -> Landmarks:
    return normalize_landmarks(
        points,
        expected_points=HAND_POINTS,
        origin_index=0,
        scale_pair=(5, 17),
        alignment_pair=(5, 17),
    )


def normalize_face(points: Landmarks) -> Landmarks:
    return normalize_landmarks(
        points,
        expected_points=FACE_POINTS,
        origin_index=1,
        scale_pair=(33, 263),
        alignment_pair=(33, 263),
    )


def resample_sequence(sequence: Sequence[Landmarks], target_frames: int = 30) -> list[Landmarks]:
    if not sequence:
        raise ValueError("A sequência não pode ser vazia.")
    if target_frames < 2:
        raise ValueError("A sequência padronizada precisa de pelo menos dois frames.")
    if len(sequence) == 1:
        return [[point[:] for point in sequence[0]] for _ in range(target_frames)]

    result: list[Landmarks] = []
    last_index = len(sequence) - 1
    for target_index in range(target_frames):
        position = target_index * last_index / (target_frames - 1)
        left_index = int(math.floor(position))
        right_index = min(left_index + 1, last_index)
        weight = position - left_index
        interpolated = [
            [
                left_coordinate + (right_coordinate - left_coordinate) * weight
                for left_coordinate, right_coordinate in zip(left_point, right_point)
            ]
            for left_point, right_point in zip(sequence[left_index], sequence[right_index])
        ]
        result.append(interpolated)
    return result


def summarize_sequence(sequence: Sequence[Landmarks]) -> list[float]:
    """Retorna posição média, desvio e deslocamento por coordenada."""
    if not sequence:
        raise ValueError("A sequência não pode ser vazia.")
    flattened = [[coordinate for point in frame for coordinate in point] for frame in sequence]
    width = len(flattened[0])
    means = [sum(frame[index] for frame in flattened) / len(flattened) for index in range(width)]
    deviations = [
        math.sqrt(sum((frame[index] - means[index]) ** 2 for frame in flattened) / len(flattened))
        for index in range(width)
    ]
    displacement = [flattened[-1][index] - flattened[0][index] for index in range(width)]
    return means + deviations + displacement


def static_manual_features(frames: list[dict]) -> list[float]:
    """Resume uma mão normalizada em 63 valores médios independentes do canal."""
    detected: list[Landmarks] = []
    for frame in frames:
        points = frame.get("right_hand") or frame.get("left_hand")
        if points:
            detected.append(normalize_hand(points))
    if not detected:
        raise ValueError("Nenhuma mão detectada na sequência.")

    flattened = [[coordinate for point in hand for coordinate in point] for hand in detected]
    features = [
        sum(hand[index] for hand in flattened) / len(flattened)
        for index in range(HAND_POINTS * 3)
    ]
    if not all(math.isfinite(value) for value in features):
        raise ValueError("Os landmarks da mão produziram características não finitas.")
    return features


def modality_features(frames: list[dict], modality: str) -> list[float]:
    if modality == "facial":
        detected = [normalize_face(frame["face"]) for frame in frames if frame.get("face")]
        normalized = resample_sequence(detected)
        return summarize_sequence(normalized)
    if modality != "manual":
        raise ValueError("Modalidade deve ser manual ou facial.")

    output: list[float] = []
    zeros = [[0.0, 0.0, 0.0] for _ in range(HAND_POINTS)]
    for hand_key in ("left_hand", "right_hand"):
        detected = [normalize_hand(frame[hand_key]) for frame in frames if frame.get(hand_key)]
        if detected:
            normalized = resample_sequence(detected)
        else:
            normalized = [zeros for _ in range(30)]
        output.extend(summarize_sequence(normalized))
    return output
