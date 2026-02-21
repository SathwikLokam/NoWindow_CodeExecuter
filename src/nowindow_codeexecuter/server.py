from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from .executor import ExecutionRequest, execute_code
from .job_queue import JobQueue


def _read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    content_length = int(handler.headers.get("Content-Length", "0"))
    raw_body = handler.rfile.read(content_length).decode("utf-8") if content_length else "{}"
    return json.loads(raw_body or "{}")


class NoWindowHandler(BaseHTTPRequestHandler):
    queue = JobQueue()

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._send_json(
                HTTPStatus.OK,
                {"status": "ok", "queue_size": self.queue.size()},
            )
            return

        if parsed.path.startswith("/jobs/"):
            job_id = parsed.path.split("/", 2)[-1]
            job = self.queue.get(job_id)
            if job is None:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "job not found"})
                return
            self._send_json(HTTPStatus.OK, job.to_dict())
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        try:
            payload = _read_json_body(self)
            request = ExecutionRequest(
                language=payload["language"],
                code=payload["code"],
                timeout_seconds=float(payload.get("timeout_seconds", 3)),
            )
        except (KeyError, ValueError, json.JSONDecodeError) as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": f"invalid payload: {exc}"})
            return

        if parsed.path == "/execute":
            try:
                result = execute_code(request)
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            self._send_json(HTTPStatus.OK, result.to_dict())
            return

        if parsed.path == "/jobs":
            try:
                job = self.queue.enqueue(request)
            except Exception as exc:
                self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                return
            self._send_json(HTTPStatus.ACCEPTED, {"job_id": job.job_id, "status": job.status})
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})


def run_server(host: str = "127.0.0.1", port: int = 8080) -> None:
    server = ThreadingHTTPServer((host, port), NoWindowHandler)
    print(f"NoWindow Code Executer server listening at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
