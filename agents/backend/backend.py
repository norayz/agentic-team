"""Backend Agent — implements code based on the architecture design."""
from pathlib import Path
from agents.shared import (
    TOOLS_ISSUE,
    TOOLS_GIT,
    TOOL_RUN_PYTHON,
    TOOL_RUN_PROJECT,
    execute_issue_tools,
    execute_git_tools,
    run_agent_service,
)

AGENT_NAME = "backend"
TOOLS = TOOLS_ISSUE + TOOLS_GIT + [TOOL_RUN_PYTHON, TOOL_RUN_PROJECT]


def tool_executor(name: str, inputs: dict) -> str:
    from tools.sandbox import run_python, run_project

    result = execute_issue_tools(name, inputs, AGENT_NAME) or execute_git_tools(name, inputs, AGENT_NAME)
    if result is not None:
        return result
    if name == "run_python":
        return str(run_python(inputs["code"], inputs.get("timeout", 30)))
    if name == "run_project":
        return str(run_project(inputs["command"], inputs.get("timeout", 60)))
    return f"Unknown tool: {name}"


def main():
    run_agent_service(
        AGENT_NAME,
        ["in-dev"],
        TOOLS,
        tool_executor,
        Path(__file__).parent / "backend.md",
    )


if __name__ == "__main__":
    main()
