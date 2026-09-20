from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import joblib

from training.bootstrap_alphabet import (
    extract_dataset,
    image_paths_by_class,
    split_train_validation_paths,
    train_bootstrap,
)


class BootstrapDatasetTest(unittest.TestCase):
    def test_rejects_directory_without_class_images(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "Nenhuma imagem de classe encontrada"):
                image_paths_by_class(Path(directory))

    def test_discovers_only_supported_images_grouped_by_class(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "B").mkdir()
            (root / "A").mkdir()
            (root / "A" / "one.png").touch()
            (root / "A" / "ignore.txt").touch()
            (root / "B" / "two.JPG").touch()

            result = image_paths_by_class(root)

        self.assertEqual(["A", "B"], list(result))
        self.assertEqual(["one.png"], [path.name for path in result["A"]])
        self.assertEqual(["two.JPG"], [path.name for path in result["B"]])

    def test_extracts_valid_images_and_counts_rejections(self) -> None:
        paths = {
            "A": [Path("a-ok.png"), Path("a-bad.png")],
            "B": [Path("b-ok.png")],
        }

        features, labels, rejected = extract_dataset(
            paths,
            limit_per_class=10,
            seed=42,
            extractor=lambda path: None if "bad" in path.name else [float(len(path.name))] * 63,
        )

        self.assertEqual(["A", "B"], labels)
        self.assertEqual(2, len(features))
        self.assertEqual({"A": 1, "B": 0}, rejected)

    def test_train_and_validation_images_do_not_overlap(self) -> None:
        paths = {"A": [Path(f"{index}.png") for index in range(10)]}

        train, validation = split_train_validation_paths(paths, 6, 3, seed=42)

        self.assertEqual(6, len(train["A"]))
        self.assertEqual(3, len(validation["A"]))
        self.assertFalse(set(train["A"]) & set(validation["A"]))


class BootstrapTrainingTest(unittest.TestCase):
    @staticmethod
    def _features(value: float, count: int) -> list[list[float]]:
        return [[value + index * 0.001] * 63 for index in range(count)]

    def test_trains_probabilistic_artifact_and_limited_report(self) -> None:
        x_train = self._features(0.0, 6) + self._features(1.0, 6)
        y_train = ["A"] * 6 + ["B"] * 6
        x_validation = self._features(0.1, 2) + self._features(0.9, 2)
        y_validation = ["A"] * 2 + ["B"] * 2
        x_test = self._features(0.2, 2) + self._features(0.8, 2)
        y_test = ["A"] * 2 + ["B"] * 2

        with tempfile.TemporaryDirectory() as directory:
            report = train_bootstrap(
                x_train,
                y_train,
                x_validation,
                y_validation,
                x_test,
                y_test,
                Path(directory),
                seed=42,
                source="fixture",
            )
            artifact = joblib.load(Path(directory) / "manual.joblib")
            persisted_report = json.loads((Path(directory) / "manual-report.json").read_text())

        self.assertEqual("manual-static-v1", artifact["feature_contract"])
        self.assertEqual(["A", "B"], artifact["classes"])
        self.assertTrue(hasattr(artifact["model"], "predict_proba"))
        self.assertTrue(artifact["model_version"].startswith("manual-static-"))
        self.assertEqual(report["model_version"], artifact["model_version"])
        self.assertEqual("provider_split_not_participant_independent", report["evaluation_scope"])
        self.assertEqual(report["model_version"], persisted_report["model_version"])

    def test_requires_at_least_two_training_classes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "duas classes"):
                train_bootstrap(
                    self._features(0.0, 4),
                    ["A"] * 4,
                    self._features(0.0, 2),
                    ["A"] * 2,
                    self._features(0.0, 2),
                    ["A"] * 2,
                    Path(directory),
                    seed=42,
                    source="fixture",
                )


if __name__ == "__main__":
    unittest.main()
