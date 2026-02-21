# NoWindow Code Executer

A full-featured, headless code execution platform that runs user-submitted snippets in isolated subprocesses with timeouts, memory limits, and both CLI and HTTP interfaces.

## Features

- **Headless execution engine** for Python, JavaScript (Node), and Bash.
- **Safety controls**: timeout, output truncation, and POSIX resource limits.
- **Job queue** for asynchronous execution with status tracking.
- **HTTP API** with endpoints for sync and async execution.
- **CLI** for local usage and server startup.
- **Comprehensive tests** for core behavior.

## Project Structure

```text
src/nowindow_codeexecuter/
  __init__.py
  cli.py
  executor.py
  job_queue.py
  server.py
tests/
  test_executor.py
  test_server.py
```

## Quick Start

### 1) Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2) Run from CLI

```bash
nwe run --language python --code "print('hello')"
```

### 3) Start API server

```bash
nwe serve --host 127.0.0.1 --port 8080
```

## HTTP API

### `GET /health`

Returns service and queue health.

### `POST /execute`

Runs code synchronously.

Request:

```json
{
  "language": "python",
  "code": "print('hello')",
  "timeout_seconds": 3
}
```

### `POST /jobs`

Creates an asynchronous job.

### `GET /jobs/<job_id>`

Returns async job status and result.

## Security Notes

This project is designed for controlled environments and local development. It is **not a hardened multi-tenant sandbox**. For production exposure, run inside containers/VMs with strong network/filesystem isolation.

## Development

```bash
pytest -q
```
