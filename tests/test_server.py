import json
import threading
import time
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

from nowindow_codeexecuter.server import NoWindowHandler


def _start_test_server() -> tuple[ThreadingHTTPServer, int]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), NoWindowHandler)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, port


def test_health_endpoint() -> None:
    server, port = _start_test_server()
    try:
        conn = HTTPConnection("127.0.0.1", port)
        conn.request("GET", "/health")
        response = conn.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
        assert response.status == 200
        assert payload["status"] == "ok"
    finally:
        server.shutdown()
        server.server_close()


def test_async_job_flow() -> None:
    server, port = _start_test_server()
    try:
        conn = HTTPConnection("127.0.0.1", port)
        body = json.dumps({"language": "python", "code": "print('job ok')"})
        conn.request("POST", "/jobs", body=body, headers={"Content-Type": "application/json"})
        created = conn.getresponse()
        created_payload = json.loads(created.read().decode("utf-8"))
        assert created.status == 202
        job_id = created_payload["job_id"]

        for _ in range(20):
            time.sleep(0.05)
            conn = HTTPConnection("127.0.0.1", port)
            conn.request("GET", f"/jobs/{job_id}")
            fetched = conn.getresponse()
            payload = json.loads(fetched.read().decode("utf-8"))
            if payload["status"] == "completed":
                assert payload["result"]["stdout"].strip() == "job ok"
                break
        else:
            raise AssertionError("job did not complete in time")
    finally:
        server.shutdown()
        server.server_close()
