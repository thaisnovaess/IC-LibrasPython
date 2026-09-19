"""Treinamento reproduzível dos classificadores manual e facial."""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from recognition.dataset import load_sample
from recognition.features import modality_features


def validate_label_counts(labels: list[str], minimum: int = 2) -> None:
    insufficient = {label: count for label, count in Counter(labels).items() if count < minimum}
    if insufficient:
        detail = ", ".join(f"{label}={count}" for label, count in sorted(insufficient.items()))
        raise ValueError(f"Classes com amostras insuficientes: {detail}.")


def split_participants(participants: list[str], seed: int = 42) -> dict[str, set[str]]:
    unique = sorted(set(participants))
    if len(unique) < 3:
        raise ValueError("São necessários pelo menos três participantes para treino, validação e teste.")
    random.Random(seed).shuffle(unique)
    test_count = max(1, round(len(unique) * 0.15))
    validation_count = max(1, round(len(unique) * 0.15))
    if test_count + validation_count >= len(unique):
        test_count = validation_count = 1
    return {
        "test": set(unique[:test_count]),
        "validation": set(unique[test_count : test_count + validation_count]),
        "train": set(unique[test_count + validation_count :]),
    }


def load_dataset(directory: Path, modality: str) -> tuple[list[list[float]], list[str], list[str]]:
    features: list[list[float]] = []
    labels: list[str] = []
    participants: list[str] = []
    label_field = "manual_label" if modality == "manual" else "facial_label"
    for path in sorted(directory.glob("sample-*.json.gz")):
        sample = load_sample(path)
        try:
            vector = modality_features(sample["frames"], modality)
        except ValueError:
            continue
        features.append(vector)
        labels.append(sample["metadata"][label_field])
        participants.append(sample["metadata"]["participant_id"])
    if not features:
        raise ValueError(f"Nenhuma amostra válida para a modalidade {modality}.")
    return features, labels, participants


def train_modality(
    samples_directory: Path,
    output_directory: Path,
    modality: str,
    seed: int = 42,
) -> dict:
    try:
        import joblib
        from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
        from sklearn.model_selection import GridSearchCV, StratifiedKFold
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.svm import SVC
    except ImportError as exc:
        raise RuntimeError(
            "O treinamento exige Python 3.11 e as dependências de requirements-vision.txt."
        ) from exc

    features, labels, participants = load_dataset(samples_directory, modality)
    validate_label_counts(labels)
    groups = split_participants(participants, seed)

    def select(group_name: str):
        indexes = [index for index, participant in enumerate(participants) if participant in groups[group_name]]
        return [features[index] for index in indexes], [labels[index] for index in indexes]

    x_train, y_train = select("train")
    x_validation, y_validation = select("validation")
    x_test, y_test = select("test")
    if not x_train or not x_validation or not x_test:
        raise ValueError("O split por participante produziu um conjunto vazio.")
    train_counts = Counter(y_train)
    folds = min(3, min(train_counts.values()))
    if folds < 2:
        raise ValueError("O conjunto de treino precisa de duas amostras por classe.")

    pipeline = Pipeline(
        [("scale", StandardScaler()), ("svm", SVC(kernel="rbf", probability=True, random_state=seed))]
    )
    search = GridSearchCV(
        pipeline,
        {"svm__C": [0.5, 1.0, 5.0], "svm__gamma": ["scale", "auto"]},
        scoring="f1_macro",
        cv=StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed),
        n_jobs=-1,
    )
    search.fit(x_train, y_train)

    validation_prediction = search.predict(x_validation)
    test_prediction = search.predict(x_test)
    classes = sorted(set(labels))
    report = {
        "modality": modality,
        "model_version": f"{modality}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "sample_count": len(labels),
        "participant_split": {name: sorted(values) for name, values in groups.items()},
        "best_parameters": search.best_params_,
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
        {"model": search.best_estimator_, "model_version": report["model_version"], "modality": modality},
        output_directory / f"{modality}.joblib",
    )
    (output_directory / f"{modality}-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Treinar classificadores de Libras")
    parser.add_argument("--samples", type=Path, default=Path("data/samples"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/models"))
    parser.add_argument("--modality", choices=("manual", "facial", "both"), default="manual")
    parser.add_argument("--seed", type=int, default=42)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    modalities = ("manual", "facial") if args.modality == "both" else (args.modality,)
    for modality in modalities:
        report = train_modality(args.samples, args.output, modality, args.seed)
        print(
            f"{modality}: acurácia de teste={report['test_accuracy']:.3f} "
            f"({report['sample_count']} amostras)"
        )


if __name__ == "__main__":
    main()
