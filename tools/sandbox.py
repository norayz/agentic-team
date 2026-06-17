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


def run_project(files: dict, entrypoint: str, timeout: int = 120) -> dict:
    """
    Creates a project from files dict, runs entrypoint command.
    files = {"main.py": "...", "requirements.txt": "..."}
    entrypoint = "python main.py" or "pytest tests/"
    Returns {stdout, stderr, exit_code, artifacts}
    Installs requirements.txt if present before running.
    """
    sbx = Sandbox(api_key=os.environ.get("E2B_API_KEY"))
    try:
        # Write all project files
        for path, content in files.items():
            sbx.files.write(f"/project/{path}", content)

        # Install requirements if present
        if "requirements.txt" in files:
            install_result = sbx.commands.run(
                "pip install -q -r /project/requirements.txt",
                timeout=120,
            )
            if install_result.exit_code != 0:
                return {
                    "stdout": install_result.stdout,
                    "stderr": install_result.stderr,
                    "exit_code": install_result.exit_code,
                    "artifacts": [],
                }

        # Run the entrypoint
        result = sbx.commands.run(
            f"cd /project && {entrypoint}",
            timeout=timeout,
        )

        artifacts = []
        try:
            sbx.commands.run("mkdir -p /tmp/output", timeout=10)
            output_files = sbx.files.list("/tmp/output")
            for f in output_files:
                content = sbx.files.read(f"/tmp/output/{f.name}")
                artifacts.append({"filename": f.name, "content": content})
        except Exception:
            pass

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.exit_code,
            "artifacts": artifacts,
        }
    finally:
        sbx.kill()
