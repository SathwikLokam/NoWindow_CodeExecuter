from __future__ import annotations

import queue
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional

from .executor import ExecutionRequest, ExecutionResult, execute_code


@dataclass(slots=True)
class Job:
    job_id: str
    request: ExecutionRequest
    status: str = "queued"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[ExecutionResult] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        payload = asdict(self)
        if self.result is not None:
            payload["result"] = self.result.to_dict()
        return payload


class JobQueue:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._queue: queue.Queue[str] = queue.Queue()
        self._lock = threading.Lock()
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

    def enqueue(self, request: ExecutionRequest) -> Job:
        job = Job(job_id=str(uuid.uuid4()), request=request)
        with self._lock:
            self._jobs[job.job_id] = job
        self._queue.put(job.job_id)
        return job

    def get(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def size(self) -> int:
        return self._queue.qsize()

    def _worker_loop(self) -> None:
        while True:
            job_id = self._queue.get()
            with self._lock:
                job = self._jobs[job_id]
                job.status = "running"
                job.started_at = datetime.now(timezone.utc).isoformat()

            try:
                result = execute_code(job.request)
                with self._lock:
                    job.result = result
                    job.status = "completed"
            except Exception as exc:  # pragma: no cover
                with self._lock:
                    job.status = "failed"
                    job.error = str(exc)
            finally:
                with self._lock:
                    job.completed_at = datetime.now(timezone.utc).isoformat()
                self._queue.task_done()
