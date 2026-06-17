import os
from e2b_code_interpreter import Sandbox


def run_python(code: str, timeout: int = 60) -> dict:
    """
    Runs Python code in isolated E2B sandbox.
    Returns {stdout: str, stderr: str, error: str|None, artifacts: list[dict]}
    artifacts = [{filename, content}] for any files written to /tmp/output/
    """
    sbx = Sandbox(api_key=os.environ.get("E2B_API_KEY"))
    try:
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
    finally:
        sbx.kill()


def run_command(command: str, timeout: int = 30) -> dict:
    """
    Runs shell command in E2B sandbox.
    Returns {stdout: str, stderr: str, exit_code: int}
    """
    sbx = Sandbox(api_key=os.environ.get("E2B_API_KEY"))
    try:
        result = sbx.commands.run(command, timeout=timeout)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.exit_code,
        }
    finally:
        sbx.kill()


def run_project(command: str, timeout: int = 120) -> dict:
    """Run a shell command in E2B sandbox. Returns {stdout, stderr, exit_code}."""
    sbx = Sandbox(api_key=os.environ.get("E2B_API_KEY"))
    try:
        result = sbx.commands.run(command, timeout=timeout)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.exit_code,
        }
    finally:
        sbx.kill()
