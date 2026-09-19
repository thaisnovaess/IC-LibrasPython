"""Coleta sincronizada de landmarks manuais e faciais pela webcam."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from recognition.dataset import SampleMetadata, save_sample


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Coletar amostra integrada de Libras")
    parser.add_argument("--participant", required=True, help="Código não identificável do participante")
    parser.add_argument("--manual-label", required=True, help="Letra ou sinal manual executado")
    parser.add_argument("--facial-label", default="neutra", help="Expressão facial executada")
    parser.add_argument("--lighting", required=True, help="Descrição curta da iluminação")
    parser.add_argument("--duration", type=float, default=3.0)
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--height", type=int, default=720)
    parser.add_argument("--fps", type=float, default=30.0)
    parser.add_argument("--output", type=Path, default=Path("data/samples"))
    parser.add_argument("--store-video", action="store_true", help="Gravar vídeo bruto com consentimento")
    return parser


def _points(landmarks) -> list[list[float]] | None:
    if landmarks is None:
        return None
    return [[point.x, point.y, point.z] for point in landmarks.landmark]


def collect(args: argparse.Namespace) -> Path:
    metadata = SampleMetadata(
        participant_id=args.participant,
        manual_label=args.manual_label,
        facial_label=args.facial_label,
        lighting=args.lighting,
        width=args.width,
        height=args.height,
        fps=args.fps,
        duration_seconds=args.duration,
        store_video=args.store_video,
    )
    metadata.validate()

    try:
        import cv2
        import mediapipe as mp
    except ImportError as exc:
        raise RuntimeError(
            "A coleta exige Python 3.11 e as dependências de requirements-vision.txt."
        ) from exc

    camera = cv2.VideoCapture(args.camera)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    camera.set(cv2.CAP_PROP_FPS, args.fps)
    if not camera.isOpened():
        raise RuntimeError("Não foi possível abrir a câmera selecionada.")

    video_writer = None
    video_path = None
    if args.store_video:
        args.output.mkdir(parents=True, exist_ok=True)
        video_path = args.output / f"video-{int(time.time())}.mp4"
        video_writer = cv2.VideoWriter(
            str(video_path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            args.fps,
            (args.width, args.height),
        )

    frames: list[dict] = []
    started_ns = time.monotonic_ns()
    holistic = mp.solutions.holistic.Holistic(
        static_image_mode=False,
        model_complexity=1,
        refine_face_landmarks=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    try:
        while (time.monotonic_ns() - started_ns) / 1_000_000_000 < args.duration:
            ok, frame = camera.read()
            if not ok:
                raise RuntimeError("A câmera deixou de fornecer frames durante a coleta.")
            if frame.shape[1] != args.width or frame.shape[0] != args.height:
                frame = cv2.resize(frame, (args.width, args.height))
            result = holistic.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            elapsed_ms = max(1, int((time.monotonic_ns() - started_ns) / 1_000_000))
            frames.append(
                {
                    "timestamp_ms": elapsed_ms,
                    "left_hand": _points(result.left_hand_landmarks),
                    "right_hand": _points(result.right_hand_landmarks),
                    "face": _points(result.face_landmarks),
                }
            )
            if video_writer is not None:
                video_writer.write(frame)
            cv2.putText(frame, "COLETANDO", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.imshow("Coleta científica de Libras", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break
    finally:
        holistic.close()
        camera.release()
        if video_writer is not None:
            video_writer.release()
        cv2.destroyAllWindows()

    sample_path = save_sample(args.output, metadata, frames)
    if video_path:
        print(f"Vídeo consentido: {video_path}")
    return sample_path


def main() -> None:
    args = build_parser().parse_args()
    path = collect(args)
    print(f"Amostra salva: {path}")


if __name__ == "__main__":
    main()
