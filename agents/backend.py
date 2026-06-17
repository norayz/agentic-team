"""Backend Agent — implements code based on the architecture design."""
import os
import time
import logging
from pathlib import Path
from agents.base import run_agent
from tools.github_issues import get_issues_by_label, update_label
from tools.models import AGENT_DEFAULTS

logger = logging.getLogger(__name__)
AGENT_NAME = "backend"
MODEL = os.environ.get("BACKEND_MODEL", AGENT_DEFAULTS["backend"])
SYSTEM_PROMPT = Path("/app/prompts/backend.md").read_text()

TOOLS = [
    {
        "name": "get_issue",
        "description": "Get issue details including title, body, labels",
        "input_schema": {"type": "object", "properties": {"issue_number": {"type": "integer"}}, "required": ["issue_number"]}
    },
    {
        "name": "get_comments",
        "description": "Get all comments on an issue",
        "input_schema": {"type": "object", "properties": {"issue_number": {"type": "integer"}}, "required": ["issue_number"]}
    },
    {
        "name": "post_comment",
        "description": "Post a comment as this agent",
        "input_schema": {"type": "object", "properties": {"issue_number": {"type": "integer"}, "message": {"type": "string"}}, "required": ["issue_number", "message"]}
    },
    {
        "name": "update_label",
        "description": "Update the status label on an issue",
        "input_schema": {"type": "object", "properties": {"issue_number": {"type": "integer"}, "new_label": {"type": "string"}}, "required": ["issue_number", "new_label"]}
    },
    {
        "name": "create_branch",
        "description": "Create a new git branch for this issue",
        "input_schema": {
            "type": "object",
            "properties": {
                "issue_number": {"type": "integer"},
                "branch_name": {"type": "string"}
            },
            "required": ["issue_number"]
        }
    },
    {
        "name": "commit_files",
        "description": "Commit one or more files to a branch",
        "input_schema": {
            "type": "object",
            "properties": {
                "branch": {"type": "string"},
                "files": {
                    "type": "array",
                    "items": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}
                },
                "message": {"type": "string"}
            },
            "required": ["branch", "files", "message"]
        }
    },
    {
        "name": "open_pr",
        "description": "Open a pull request from branch to main",
        "input_schema": {
            "type": "object",
            "properties": {
                "branch": {"type": "string"},
                "title": {"type": "string"},
                "body": {"type": "string"},
                "issue_number": {"type": "integer"}
            },
            "required": ["branch", "title", "body"]
        }
    },
    {
        "name": "run_python",
        "description": "Execute Python code in a sandbox and return stdout/stderr",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "timeout": {"type": "integer", "description": "Timeout in seconds, default 30"}
            },
            "required": ["code"]
        }
    },
    {
        "name": "run_project",
        "description": "Run a shell command inside the workspace project directory",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "timeout": {"type": "integer", "description": "Timeout in seconds, default 60"}
            },
            "required": ["command"]
        }
    },
]


def tool_executor(name: str, inputs: dict) -> str:
    from tools.github_issues import get_issue, get_comments, post_comment, update_label
    from tools.git import create_agent_branch, commit_files, open_pr
    from tools.sandbox import run_python, run_project
    from github import Github

    if name == "get_issue":
        return str(get_issue(inputs["issue_number"]))
    elif name == "get_comments":
        return str(get_comments(inputs["issue_number"]))
    elif name == "post_comment":
        post_comment(inputs["issue_number"], AGENT_NAME, inputs["message"])
        return "Comment posted"
    elif name == "update_label":
        update_label(inputs["issue_number"], inputs["new_label"])
        return f"Label updated to {inputs['new_label']}"
    elif name == "create_branch":
        branch_name = inputs.get("branch_name") or f"backend/issue-{inputs['issue_number']}"
        result = create_agent_branch(inputs["issue_number"], branch_name)
        return str(result)
    elif name == "commit_files":
        result = commit_files(inputs["branch"], inputs["files"], inputs["message"])
        return str(result)
    elif name == "open_pr":
        result = open_pr(inputs["branch"], inputs["title"], inputs["body"], inputs.get("issue_number"))
        return str(result)
    elif name == "run_python":
        result = run_python(inputs["code"], inputs.get("timeout", 30))
        return str(result)
    elif name == "run_project":
        result = run_project(inputs["command"], inputs.get("timeout", 60))
        return str(result)
    return f"Unknown tool: {name}"


def main():
    logging.basicConfig(level=logging.INFO)
    logger.info("Backend agent started, polling for work...")
    while True:
        try:
            issues = get_issues_by_label("in-dev")
            for issue in issues:
                logger.info(f"Backend picking up issue #{issue['number']}")
                run_agent(issue["number"], AGENT_NAME, MODEL, TOOLS, SYSTEM_PROMPT, tool_executor)
        except Exception as e:
            logger.error(f"Backend agent error: {e}")
        time.sleep(10)


if __name__ == "__main__":
    main()
