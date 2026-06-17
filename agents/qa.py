"""QA Agent — writes and runs tests against the implemented code."""
import os
from pathlib import Path
from agents.base import run_agent
from agents.shared import TOOLS_ISSUE, TOOLS_GIT, execute_issue_tools, execute_git_tools, poll
from tools.models import AGENT_DEFAULTS

AGENT_NAME = "qa"
MODEL = os.environ.get("QA_MODEL", AGENT_DEFAULTS["qa"])
SYSTEM_PROMPT = Path("/app/prompts/qa.md").read_text()

TOOL_RUN_PROJECT = {
    "name": "run_project",
    "description": "Run a shell command in the sandbox (for test execution)",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {"type": "string"},
            "timeout": {"type": "integer", "description": "Seconds, default 120"},
        },
        "required": ["command"],
    },
}

TOOLS = TOOLS_ISSUE + TOOLS_GIT + [TOOL_RUN_PROJECT]


def tool_executor(name: str, inputs: dict) -> str:
    from tools.sandbox import run_project

    result = execute_issue_tools(name, inputs, AGENT_NAME) or execute_git_tools(name, inputs, AGENT_NAME)
    if result is not None:
        return result
    if name == "run_project":
        return str(run_project(inputs["command"], inputs.get("timeout", 120)))
    return f"Unknown tool: {name}"


def handle(issue: dict) -> None:
    run_agent(issue["number"], AGENT_NAME, MODEL, TOOLS, SYSTEM_PROMPT, tool_executor)


def main():
    poll(AGENT_NAME, ["in-qa"], handle)


if __name__ == "__main__":
    main()
