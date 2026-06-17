"""DevOps Agent — sets up CI/CD, Docker, and infra config in parallel with backend."""
import os
import time
import logging
from pathlib import Path
from agents.base import run_agent
from tools.github_issues import get_issues_by_label, update_label
from tools.models import AGENT_DEFAULTS

logger = logging.getLogger(__name__)
AGENT_NAME = "devops"
MODEL = os.environ.get("DEVOPS_MODEL", AGENT_DEFAULTS["devops"])
SYSTEM_PROMPT = Path("/app/prompts/devops.md").read_text()

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
        "name": "check_branch_exists",
        "description": "Check if a git branch exists in the repository",
        "input_schema": {
            "type": "object",
            "properties": {
                "branch_name": {"type": "string"}
            },
            "required": ["branch_name"]
        }
    },
    {
        "name": "create_branch",
        "description": "Create a new git branch for devops work",
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
        "description": "Commit Dockerfile, CI config, and infra files to a branch",
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
        "description": "Open a pull request for infra/devops changes",
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
        "name": "run_command",
        "description": "Run a shell command in the sandbox to verify docker builds or infra scripts",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "timeout": {"type": "integer", "description": "Timeout in seconds, default 120"}
            },
            "required": ["command"]
        }
    },
]


def tool_executor(name: str, inputs: dict) -> str:
    from tools.github_issues import get_issue, get_comments, post_comment, update_label
    from tools.git import create_agent_branch, commit_files, open_pr
    from tools.sandbox import run_project
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
    elif name == "check_branch_exists":
        g = Github(os.environ["GITHUB_TOKEN"])
        repo = g.get_repo(os.environ["GITHUB_REPO"])
        try:
            repo.get_branch(inputs["branch_name"])
            return f"Branch '{inputs['branch_name']}' exists"
        except Exception:
            return f"Branch '{inputs['branch_name']}' does not exist"
    elif name == "create_branch":
        branch_name = inputs.get("branch_name") or f"devops/issue-{inputs['issue_number']}"
        result = create_agent_branch(inputs["issue_number"], branch_name)
        return str(result)
    elif name == "commit_files":
        result = commit_files(inputs["branch"], inputs["files"], inputs["message"])
        return str(result)
    elif name == "open_pr":
        result = open_pr(inputs["branch"], inputs["title"], inputs["body"], inputs.get("issue_number"))
        return str(result)
    elif name == "run_command":
        result = run_project(inputs["command"], inputs.get("timeout", 120))
        return str(result)
    return f"Unknown tool: {name}"


def main():
    logging.basicConfig(level=logging.INFO)
    logger.info("DevOps agent started, polling for work...")
    while True:
        try:
            issues = get_issues_by_label("in-dev")
            for issue in issues:
                # Check if backend branch exists before acting — devops runs in parallel with backend
                from github import Github
                g = Github(os.environ["GITHUB_TOKEN"])
                repo = g.get_repo(os.environ["GITHUB_REPO"])
                backend_branch = f"backend/issue-{issue['number']}"
                try:
                    repo.get_branch(backend_branch)
                    logger.info(f"DevOps picking up issue #{issue['number']} (backend branch exists)")
                    run_agent(issue["number"], AGENT_NAME, MODEL, TOOLS, SYSTEM_PROMPT, tool_executor)
                except Exception:
                    logger.info(f"DevOps skipping issue #{issue['number']} — backend branch not yet created")
        except Exception as e:
            logger.error(f"DevOps agent error: {e}")
        time.sleep(10)


if __name__ == "__main__":
    main()
