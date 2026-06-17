"""Backend Agent — implements code based on the architecture design."""
import os
from pathlib import Path
from agents.base import run_agent
from agents.shared import TOOLS_ISSUE, TOOLS_GIT, execute_issue_tools, execute_git_tools, poll
from tools.models import AGENT_DEFAULTS

AGENT_NAME = "backend"
MODEL = os.environ.get("BACKEND_MODEL", AGENT_DEFAULTS["backend"])
SYSTEM_PROMPT = Path("/app/prompts/backend.md").read_text()

TOOL_RUN_PYTHON = {
    "name": "run_python",
    "description": "Execute Python code in an E2B sandbox; returns stdout + stderr",
    "input_schema": {
        "type": "object",
        "properties": {
            "code": {"type": "string"},
            "timeout": {"type": "integer", "description": "Seconds, default 30"},
        },
        "required": ["code"],
    },
}

TOOL_RUN_PROJECT = {
    "name": "run_project",
    "description": "Run a shell command inside the sandbox workspace directory",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {"type": "string"},
            "timeout": {"type": "integer", "description": "Seconds, default 60"},
        },
        "required": ["command"],
    },
}

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


def handle(issue: dict) -> None:
    run_agent(issue["number"], AGENT_NAME, MODEL, TOOLS, SYSTEM_PROMPT, tool_executor)


def main():
    poll(AGENT_NAME, ["in-dev"], handle)


if __name__ == "__main__":
    main()
