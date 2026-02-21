from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import textwrap
import time
from dataclasses import asdict, dataclass
from typing import Callable


MAX_OUTPUT_BYTES = 64_000


@dataclass(slots=True)
class ExecutionRequest:
    language: str
    code: str
    timeout_seconds: float = 3.0


@dataclass(slots=True)
class ExecutionResult:
    language: str
    return_code: int
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool

    def to_dict(self) -> dict:
        return asdict(self)


def _apply_resource_limits() -> None:
    try:
        import resource

        # Memory limit: 256 MB
        resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))
        # CPU limit: 5 seconds hard.
        resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
    except Exception:
        # Best-effort only (works mainly on Unix).
        pass


def _normalize_script(code: str) -> str:
    return textwrap.dedent(code).strip() + "\n"


def _resolve_command(language: str, source_path: str) -> list[str]:
    normalized = language.lower().strip()
    commands: dict[str, Callable[[str], list[str]]] = {
        "python": lambda p: ["python3", p],
        "py": lambda p: ["python3", p],
        "javascript": lambda p: ["node", p],
        "js": lambda p: ["node", p],
        "bash": lambda p: ["bash", p],
        "sh": lambda p: ["bash", p],
    }
    if normalized not in commands:
        raise ValueError(f"Unsupported language '{language}'. Use python, javascript, or bash.")
    return commands[normalized](source_path)


def execute_code(request: ExecutionRequest) -> ExecutionResult:
    start = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="nwe-") as tmp_dir:
        extension = {
            "python": ".py",
            "py": ".py",
            "javascript": ".js",
            "js": ".js",
            "bash": ".sh",
            "sh": ".sh",
        }.get(request.language.lower().strip(), ".txt")

        source_file = os.path.join(tmp_dir, f"snippet{extension}")
        with open(source_file, "w", encoding="utf-8") as handle:
            handle.write(_normalize_script(request.code))

        command = _resolve_command(request.language, source_file)
        executable = shutil.which(command[0])
        if executable is None:
            raise RuntimeError(f"Required runtime '{command[0]}' not found in PATH")

        timed_out = False
        try:
            completed = subprocess.run(
                command,
                cwd=tmp_dir,
                text=True,
                capture_output=True,
                timeout=request.timeout_seconds,
                preexec_fn=_apply_resource_limits if os.name == "posix" else None,
                env={"PATH": os.environ.get("PATH", "")},
            )
            stdout = completed.stdout[:MAX_OUTPUT_BYTES]
            stderr = completed.stderr[:MAX_OUTPUT_BYTES]
            return_code = completed.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout = (exc.stdout or "")[:MAX_OUTPUT_BYTES]
            stderr = ((exc.stderr or "") + "\nExecution timed out.")[:MAX_OUTPUT_BYTES]
            return_code = 124

    duration_ms = int((time.perf_counter() - start) * 1000)
    return ExecutionResult(
        language=request.language,
        return_code=return_code,
        stdout=stdout,
        stderr=stderr,
        duration_ms=duration_ms,
        timed_out=timed_out,
    )
