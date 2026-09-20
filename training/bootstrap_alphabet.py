"""Treina um baseline local de letras estáticas a partir de imagens públicas."""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from recognition.features import static_manual_features


SUPPORTED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
FEATURE_CONTRACT = "manual-static-v1"
SOURCE_REFERENCE = "https://www.kaggle.com/datasets/williansoliveira/libras"


def image_paths_by_class(directory: Path) -> dict[str, list[Path]]:
    if not directory.is_dir():
        raise ValueError(f"Diretório de imagens não encontrado: {directory}")
    result: dict[str, list[Path]] = {}
    for class_directory in sorted(path for path in directory.iterdir() if path.is_dir()):
        images = sorted(
            path
            for path in class_directory.iterdir()
            if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES
        )
        if images:
            result[class_directory.name.upper()] = images
    if not result:
        raise ValueError(f"Nenhuma imagem de classe encontrada em {directory}.")
    return result


def split_train_validation_paths(
    paths_by_class: dict[str, list[Path]],
    train_per_class: int,
    validation_per_class: int,
    *,
    seed: int,
) -> tuple[dict[str, list[Path]], dict[str, list[Path]]]:
    train: dict[str, list[Path]] = {}
    validation: dict[str, list[Path]] = {}
    for label, paths in paths_by_class.items():
        shuffled = paths[:]
        random.Random(f"{seed}:{label}").shuffle(shuffled)
        train[label] = shuffled[:train_per_class]
        validation[label] = shuffled[train_per_class : train_per_class + validation_per_class]
    return train, validation


def extract_dataset(
    paths_by_class: dict[str, list[Path]],
    *,
    limit_per_class: int,
    seed: int,
    extractor: Callable[[Path], list[float] | None],
) -> tuple[list[list[float]], list[str], dict[str, int]]:
    features: list[list[float]] = []
    labels: list[str] = []
    rejected: dict[str, int] = {}
    for label, paths in sorted(paths_by_class.items()):
        selected = paths[:]
        random.Random(f"{seed}:{label}").shuffle(selected)
        rejected[label] = 0
        for path in selected[:limit_per_class]:
            vector = extractor(path)
            if vector is None:
                rejected[label] += 1
                continue
            if len(vector) != 63:
                raise ValueError(f"Feature inválida para {path}: esperados 63 valores.")
            features.append(vector)
            labels.append(label)
    return features, labels, rejected


def extract_image_feature(path: Path, hands, cv2) -> list[float] | None:
    image = cv2.imread(str(path))
    if image is None:
        return None
    resized = cv2.resize(image, (512, 512), interpolation=cv2.INTER_CUBIC)
    result = hands.process(cv2.cvtColor(resized, cv2.COLOR_BGR2RGB))
    if not result.multi_hand_landmarks:
        return None
    points = [
        [point.x, point.y, point.z]
        for point in result.multi_hand_landmarks[0].landmark
    ]
    try:
        return static_manual_features([{"left_hand": None, "right_hand": points}])
    except ValueError:
        return None


def _validate_training_sets(
    x_train: list[list[float]],
    y_train: list[str],
    x_validation: list[list[float]],
    y_validation: list[str],
    x_test: list[list[float]],
    y_test: list[str],
) -> list[str]:
    if not (len(x_train) == len(y_train) and len(x_validation) == len(y_validation) and len(x_test) == len(y_test)):
        raise ValueError("Features e rótulos possuem tamanhos incompatíveis.")
    classes = sorted(set(y_train))
    if len(classes) < 2:
        raise ValueError("O bootstrap exige pelo menos duas classes no treino.")
    if not x_validation or not x_test:
        raise ValueError("Validação e teste precisam conter amostras válidas.")
    insufficient = {label: count for label, count in Counter(y_train).items() if count < 2}
    if insufficient:
        raise ValueError(f"Classes sem duas amostras de treino: {insufficient}")
    return classes


def train_bootstrap(
    x_train: list[list[float]],
    y_train: list[str],
    x_validation: list[list[float]],
    y_validation: list[str],
    x_test: list[list[float]],
    y_test: list[str],
    output_directory: Path,
    *,
    seed: int,
    source: str,
) -> dict:
    import joblib
    from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.svm import SVC

    classes = _validate_training_sets(
        x_train, y_train, x_validation, y_validation, x_test, y_test
    )
    model = Pipeline(
        [
            ("scale", StandardScaler()),
            ("svm", SVC(kernel="rbf", C=5.0, gamma="scale", probability=True, random_state=seed)),
        ]
    )
    model.fit(x_train, y_train)
    validation_prediction = model.predict(x_validation)
    test_prediction = model.predict(x_test)
    model_version = f"manual-static-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    report = {
        "modality": "manual",
        "feature_contract": FEATURE_CONTRACT,
        "model_version": model_version,
        "source": source,
        "evaluation_scope": "provider_split_not_participant_independent",
        "classes": classes,
        "sample_count": {
            "train": len(y_train),
            "validation": len(y_validation),
            "test": len(y_test),
        },
        "validation_accuracy": accuracy_score(y_validation, validation_prediction),
        "test_accuracy": accuracy_score(y_test, test_prediction),
        "test_classification": classification_report(
            y_test, test_prediction, labels=classes, output_dict=True, zero_division=0
        ),
        "confusion_labels": classes,
        "confusion_matrix": confusion_matrix(y_test, test_prediction, labels=classes).tolist(),
    }
    output_directory.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": model,
            "model_version": model_version,
            "modality": "manual",
            "feature_contract": FEATURE_CONTRACT,
            "classes": classes,
            "source": source,
        },
        output_directory / "manual.joblib",
    )
    (output_directory / "manual-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Treinar baseline do alfabeto estático de Libras")
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("artifacts/models"))
    parser.add_argument("--train-per-class", type=int, default=80)
    parser.add_argument("--validation-per-class", type=int, default=20)
    parser.add_argument("--test-per-class", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if min(args.train_per_class, args.validation_per_class, args.test_per_class) < 1:
        raise ValueError("Os limites por classe precisam ser positivos.")

    import cv2
    import mediapipe as mp

    provider_train = image_paths_by_class(args.dataset / "train")
    provider_test = image_paths_by_class(args.dataset / "test")
    train_paths, validation_paths = split_train_validation_paths(
        provider_train,
        args.train_per_class,
        args.validation_per_class,
        seed=args.seed,
    )
    hands = mp.solutions.hands.Hands(
        static_image_mode=True,
        max_num_hands=1,
        model_complexity=1,
        min_detection_confidence=0.3,
    )
    try:
        extractor = lambda path: extract_image_feature(path, hands, cv2)
        x_train, y_train, rejected_train = extract_dataset(
            train_paths,
            limit_per_class=args.train_per_class,
            seed=args.seed,
            extractor=extractor,
        )
        x_validation, y_validation, rejected_validation = extract_dataset(
            validation_paths,
            limit_per_class=args.validation_per_class,
            seed=args.seed + 1,
            extractor=extractor,
        )
        x_test, y_test, rejected_test = extract_dataset(
            provider_test,
            limit_per_class=args.test_per_class,
            seed=args.seed + 2,
            extractor=extractor,
        )
    finally:
        hands.close()

    report = train_bootstrap(
        x_train,
        y_train,
        x_validation,
        y_validation,
        x_test,
        y_test,
        args.output,
        seed=args.seed,
        source=SOURCE_REFERENCE,
    )
    print(json.dumps({
        "model_version": report["model_version"],
        "classes": report["classes"],
        "sample_count": report["sample_count"],
        "validation_accuracy": report["validation_accuracy"],
        "test_accuracy": report["test_accuracy"],
        "rejected": {
            "train": rejected_train,
            "validation": rejected_validation,
            "test": rejected_test,
        },
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
