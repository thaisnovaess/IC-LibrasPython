"""Servidor HTTP local, sem dependências externas, para o MVP web."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from database.communication import CommunicationRepository
from database.db import DB_PATH
from models.recognizer import build_recognizer
from webapp.application import CommunicationApplication, ValidationError


STATIC_DIR = Path(__file__).resolve().parent / "static"
MAX_BODY_BYTES = 2 * 1024 * 1024


class RequestHandler(BaseHTTPRequestHandler):
    application: CommunicationApplication

    def _json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        raw_length = self.headers.get("Content-Length", "0")
        try:
            length = int(raw_length)
        except ValueError as exc:
            raise ValidationError("Tamanho de requisição inválido.") from exc
        if length <= 0 or length > MAX_BODY_BYTES:
            raise ValidationError("Corpo da requisição vazio ou muito grande.")
        try:
            payload = json.loads(self.rfile.read(length))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValidationError("JSON inválido.") from exc
        if not isinstance(payload, dict):
            raise ValidationError("O JSON deve ser um objeto.")
        return payload

    def _serve_static(self, request_path: str) -> None:
        relative = "index.html" if request_path == "/" else unquote(request_path.lstrip("/"))
        candidate = (STATIC_DIR / relative).resolve()
        if STATIC_DIR.resolve() not in candidate.parents and candidate != STATIC_DIR.resolve():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not candidate.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = candidate.read_bytes()
        content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            if path == "/api/status":
                self._json(HTTPStatus.OK, self.application.status())
                return
            if path.startswith("/api/sessions/"):
                session_id = path.removeprefix("/api/sessions/")
                self._json(HTTPStatus.OK, self.application.session(session_id))
                return
            self._serve_static(path)
        except LookupError as exc:
            self._json(HTTPStatus.NOT_FOUND, {"error": str(exc)})
        except Exception:
            self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "Erro interno inesperado."})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            if path == "/api/sessions":
                self._json(HTTPStatus.CREATED, self.application.create_session())
                return
            if path == "/api/events":
                self._json(HTTPStatus.CREATED, self.application.add_event(self._read_json()))
                return
            if path == "/api/predict":
                frames = None
                if int(self.headers.get("Content-Length", "0")) > 0:
                    request = self._read_json()
                    encoded_frames = request.get("frames")
                    if not isinstance(encoded_frames, list) or not 1 <= len(encoded_frames) <= 30:
                        raise ValidationError("Envie entre 1 e 30 imagens na sequência.")
                    frames = []
                    for encoded in encoded_frames:
                        if not isinstance(encoded, str) or "," not in encoded:
                            raise ValidationError("Imagem em formato data URL inválido.")
                        try:
                            image = base64.b64decode(encoded.split(",", 1)[1], validate=True)
                        except (ValueError, base64.binascii.Error) as exc:
                            raise ValidationError("Imagem em base64 inválida.") from exc
                        if not image or len(image) > MAX_BODY_BYTES:
                            raise ValidationError("Cada imagem deve possuir no máximo 2 MB.")
                        frames.append(image)
                status, payload = self.application.predict(frames)
                self._json(status, payload)
                return
            self._json(HTTPStatus.NOT_FOUND, {"error": "Rota não encontrada."})
        except ValidationError as exc:
            self._json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        except LookupError as exc:
            self._json(HTTPStatus.NOT_FOUND, {"error": str(exc)})
        except Exception:
            self._json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "Erro interno inesperado."})

    def log_message(self, format: str, *args: object) -> None:
        print(f"[{self.log_date_time_string()}] {format % args}")


def build_server(host: str, port: int, database_path: str | Path) -> ThreadingHTTPServer:
    application = CommunicationApplication(
        CommunicationRepository(database_path),
        recognizer=build_recognizer(),
    )
    handler = type("ConfiguredRequestHandler", (RequestHandler,), {"application": application})
    return ThreadingHTTPServer((host, port), handler)


def main() -> None:
    parser = argparse.ArgumentParser(description="Interface local de Libras para texto")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--database", default=None)
    args = parser.parse_args()

    database_path = args.database or DB_PATH
    server = build_server(args.host, args.port, database_path)
    print(f"Interface disponível em http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
