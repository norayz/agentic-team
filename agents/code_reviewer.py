"""Code Reviewer Agent — reviews pull requests for correctness, style, and security."""
import os
from pathlib import Path
from agents.base import run_agent
from agents.shared import TOOLS_ISSUE, execute_issue_tools, poll
from tools.models import AGENT_DEFAULTS

AGENT_NAME = "code_reviewer"
MODEL = os.environ.get("CR_MODEL", AGENT_DEFAULTS["code_reviewer"])
SYSTEM_PROMPT = Path("/app/prompts/code_reviewer.md").read_text()

TOOL_GET_PR_FILES = {
    "name": "get_pr_files",
    "description": "List files changed in a PR with diffs; optionally include full file content",
    "input_schema": {
        "type": "object",
        "properties": {
            "pr_number": {"type": "integer"},
            "include_content": {"type": "boolean", "description": "Fetch full file content from the PR branch"},
        },
        "required": ["pr_number"],
    },
}

TOOL_POST_PR_REVIEW = {
    "name": "post_pr_review",
    "description": "Submit a PR review verdict",
    "input_schema": {
        "type": "object",
        "properties": {
            "pr_number": {"type": "integer"},
            "body": {"type": "string"},
            "event": {"type": "string", "enum": ["APPROVE", "REQUEST_CHANGES", "COMMENT"]},
        },
        "required": ["pr_number", "body", "event"],
    },
}

TOOLS = TOOLS_ISSUE + [TOOL_GET_PR_FILES, TOOL_POST_PR_REVIEW]


def tool_executor(name: str, inputs: dict) -> str:
    from tools.git import get_pr_files, post_pr_review

    result = execute_issue_tools(name, inputs, AGENT_NAME)
    if result is not None:
        return result
    if name == "get_pr_files":
        return str(get_pr_files(inputs["pr_number"], inputs.get("include_content", False)))
    if name == "post_pr_review":
        post_pr_review(inputs["pr_number"], inputs["body"], inputs["event"])
        return f"Review posted ({inputs['event']})"
    return f"Unknown tool: {name}"


def handle(issue: dict) -> None:
    run_agent(issue["number"], AGENT_NAME, MODEL, TOOLS, SYSTEM_PROMPT, tool_executor)


def main():
    poll(AGENT_NAME, ["cr-review"], handle)


if __name__ == "__main__":
    main()
