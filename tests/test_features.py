from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from recognition.dataset import SampleMetadata, load_sample, save_sample, validate_frames
from recognition.features import modality_features, normalize_face, normalize_hand, resample_sequence


def landmarks(count: int, offset: float = 0.0) -> list[list[float]]:
    return [[offset + index * 0.01, offset + (index % 7) * 0.02, index * 0.001] for index in range(count)]


class DatasetTest(unittest.TestCase):
    def test_requires_collection_metadata(self) -> None:
        metadata = SampleMetadata("", "A", "neutra", "uniforme", 1280, 720, 30, 2)

        with self.assertRaisesRegex(ValueError, "participant_id"):
            metadata.validate()

    def test_rejects_wrong_landmark_count(self) -> None:
        with self.assertRaisesRegex(ValueError, "21"):
            validate_frames([{"timestamp_ms": 1, "left_hand": landmarks(20)}])

    def test_rejects_out_of_order_timestamps(self) -> None:
        frames = [{"timestamp_ms": 2}, {"timestamp_ms": 1}]

        with self.assertRaisesRegex(ValueError, "timestamps"):
            validate_frames(frames)

    def test_round_trips_compressed_sample(self) -> None:
        metadata = SampleMetadata("p01", "A", "neutra", "uniforme", 1280, 720, 30, 2)
        frames = [{"timestamp_ms": 1, "left_hand": landmarks(21), "face": landmarks(468)}]
        with tempfile.TemporaryDirectory() as directory:
            path = save_sample(directory, metadata, frames)
            loaded = load_sample(path)

        self.assertEqual("A", loaded["metadata"]["manual_label"])
        self.assertEqual(468, len(loaded["frames"][0]["face"]))


class FeatureTest(unittest.TestCase):
    def test_normalizes_hand_origin_and_scale(self) -> None:
        result = normalize_hand(landmarks(21))

        self.assertEqual([0.0, 0.0, 0.0], result[0])
        self.assertAlmostEqual(1.0, ((result[5][0] - result[17][0]) ** 2 + (result[5][1] - result[17][1]) ** 2 + (result[5][2] - result[17][2]) ** 2) ** 0.5)

    def test_normalizes_face_to_468_points(self) -> None:
        result = normalize_face(landmarks(468))

        self.assertEqual(468, len(result))
        self.assertEqual([0.0, 0.0, 0.0], result[1])

    def test_resamples_sequence_to_30_frames(self) -> None:
        sequence = [landmarks(21, 0.0), landmarks(21, 1.0)]

        result = resample_sequence(sequence)

        self.assertEqual(30, len(result))
        self.assertEqual(sequence[0], result[0])
        self.assertEqual(sequence[-1], result[-1])

    def test_manual_features_keep_two_hand_channels(self) -> None:
        frames = [{"left_hand": landmarks(21), "right_hand": None}]

        result = modality_features(frames, "manual")

        self.assertEqual(21 * 3 * 3 * 2, len(result))

    def test_facial_features_use_468_points(self) -> None:
        result = modality_features([{"face": landmarks(468)}], "facial")

        self.assertEqual(468 * 3 * 3, len(result))
