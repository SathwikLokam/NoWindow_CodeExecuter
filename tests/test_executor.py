from nowindow_codeexecuter.executor import ExecutionRequest, execute_code


def test_python_execution_success() -> None:
    result = execute_code(ExecutionRequest(language="python", code="print('hello')"))
    assert result.return_code == 0
    assert result.stdout.strip() == "hello"
    assert result.timed_out is False


def test_unsupported_language() -> None:
    try:
        execute_code(ExecutionRequest(language="ruby", code="puts 'x'"))
    except ValueError as exc:
        assert "Unsupported language" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_timeout() -> None:
    code = "import time\ntime.sleep(2)\nprint('done')"
    result = execute_code(ExecutionRequest(language="python", code=code, timeout_seconds=0.1))
    assert result.timed_out is True
    assert result.return_code == 124
