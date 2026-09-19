from __future__ import annotations

import unittest

from training.collect import build_parser as collection_parser
from training.train import split_participants, validate_label_counts


class CollectionContractTest(unittest.TestCase):
    def test_video_storage_is_opt_in(self) -> None:
        args = collection_parser().parse_args(
            ["--participant", "p01", "--manual-label", "A", "--lighting", "uniforme"]
        )

        self.assertFalse(args.store_video)
        self.assertEqual("neutra", args.facial_label)

    def test_rejects_missing_required_metadata(self) -> None:
        with self.assertRaises(SystemExit):
            collection_parser().parse_args(["--manual-label", "A"])


class TrainingContractTest(unittest.TestCase):
    def test_splits_participants_without_overlap(self) -> None:
        result = split_participants([f"p{index:02}" for index in range(10)])

        self.assertFalse(result["train"] & result["validation"])
        self.assertFalse(result["train"] & result["test"])
        self.assertFalse(result["validation"] & result["test"])
        self.assertEqual(10, len(result["train"] | result["validation"] | result["test"]))

    def test_requires_three_participants(self) -> None:
        with self.assertRaisesRegex(ValueError, "três participantes"):
            split_participants(["p01", "p02"])

    def test_identifies_classes_with_insufficient_samples(self) -> None:
        with self.assertRaisesRegex(ValueError, "B=1"):
            validate_label_counts(["A", "A", "B"])
