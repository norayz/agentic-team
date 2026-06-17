"""Code Reviewer Agent — reviews pull requests for correctness, style, and security."""
from pathlib import Path
from agents.shared import (
    TOOLS_ISSUE,
    TOOL_GET_PR_FILES,
    TOOL_POST_PR_REVIEW,
    execute_issue_tools,
    run_agent_service,
)

AGENT_NAME = "code_reviewer"
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


def main():
    run_agent_service(
        AGENT_NAME,
        ["cr-review"],
        TOOLS,
        tool_executor,
        Path(__file__).parent / "code_reviewer.md",
    )


if __name__ == "__main__":
    main()
