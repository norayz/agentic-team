"""Persistent E2B sandbox manager — one sandbox per session (issue number)."""
import os
import time
import threading
from e2b_code_interpreter import Sandbox

_sandboxes: dict[str, dict] = {}  # key -> {"sandbox": Sandbox, "last_used": float}
_lock = threading.Lock()
_IDLE_TIMEOUT = 300  # kill sandbox after 5 min idle


def _get_or_create(session_id: str) -> Sandbox:
    """Get existing sandbox or create new one for this session."""
    with _lock:
        entry = _sandboxes.get(session_id)
        if entry is not None:
            entry["last_used"] = time.time()
            return entry["sandbox"]
        sbx = Sandbox(api_key=os.environ.get("E2B_API_KEY"))
        _sandboxes[session_id] = {"sandbox": sbx, "last_used": time.time()}
        return sbx


def close_sandbox(session_id: str) -> None:
    """Explicitly close a sandbox when done with an issue."""
    with _lock:
        entry = _sandboxes.pop(session_id, None)
    if entry:
        entry["sandbox"].kill()


def _cleanup_idle():
    """Background thread that kills idle sandboxes."""
    while True:
        time.sleep(60)
        now = time.time()
        to_close = []
        with _lock:
            for key, entry in list(_sandboxes.items()):
                if now - entry["last_used"] > _IDLE_TIMEOUT:
                    to_close.append(_sandboxes.pop(key))
        for entry in to_close:
            try:
                entry["sandbox"].kill()
            except Exception:
                pass


threading.Thread(target=_cleanup_idle, daemon=True).start()


def run_python(code: str, timeout: int = 60, session_id: str = "default") -> dict:
    """
    Runs Python code in a persistent E2B sandbox.
    Returns {stdout: str, stderr: str, error: str|None, artifacts: list[dict]}
    artifacts = [{filename, content}] for any files written to /tmp/output/
    """
    sbx = _get_or_create(session_id)
    execution = sbx.run_code(code, timeout=timeout)
    stdout = "\n".join(str(out) for out in execution.logs.stdout)
    stderr = "\n".join(str(err) for err in execution.logs.stderr)
    error = execution.error.value if execution.error else None

    artifacts = []
    try:
        output_files = sbx.files.list("/tmp/output")
        for f in output_files:
            content = sbx.files.read(f"/tmp/output/{f.name}")
            artifacts.append({"filename": f.name, "content": content})
    except Exception:
        pass

    return {
        "stdout": stdout,
        "stderr": stderr,
        "error": error,
        "artifacts": artifacts,
    }


def run_project(command: str, timeout: int = 120, session_id: str = "default") -> dict:
    """Run a shell command in a persistent E2B sandbox. Returns {stdout, stderr, exit_code}."""
    sbx = _get_or_create(session_id)
    result = sbx.commands.run(command, timeout=timeout)
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exit_code": result.exit_code,
    }
