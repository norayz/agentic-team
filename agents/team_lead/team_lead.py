"""Team Lead Agent — reviews PM specs, arch designs, and final PRs before handoff."""
from pathlib import Path
from agents.shared import (
    TOOLS_ISSUE,
    TOOL_GET_PR_FILES,
    TOOL_POST_PR_REVIEW,
    TOOL_CREATE_SUB_ISSUE,
    TOOL_MERGE_PR,
    execute_issue_tools,
    run_agent_service,
)

AGENT_NAME = "team_lead"
TOOLS = TOOLS_ISSUE + [TOOL_GET_PR_FILES, TOOL_POST_PR_REVIEW, TOOL_CREATE_SUB_ISSUE, TOOL_MERGE_PR]


def tool_executor(name: str, inputs: dict) -> str:
    from tools.github_issues import create_sub_issue
    from tools.git import get_pr_files, post_pr_review, merge_pr

    result = execute_issue_tools(name, inputs, AGENT_NAME)
    if result is not None:
        return result
    if name == "get_pr_files":
        return str(get_pr_files(inputs["pr_number"], inputs.get("include_content", False)))
    if name == "post_pr_review":
        post_pr_review(inputs["pr_number"], inputs["body"], inputs["event"])
        return f"PR #{inputs['pr_number']} review posted ({inputs['event']})"
    if name == "create_sub_issue":
        n = create_sub_issue(
            inputs["parent_issue_number"], inputs["title"], inputs["body"], inputs.get("label")
        )
        return f"Sub-issue #{n} created"
    if name == "merge_pr":
        merge_pr(inputs["pr_number"], inputs.get("merge_method", "squash"))
        return f"PR #{inputs['pr_number']} merged"
    return f"Unknown tool: {name}"


def main():
    run_agent_service(
        AGENT_NAME,
        ["tl-pm-review", "tl-arch-review", "tl-final-review"],
        TOOLS,
        tool_executor,
        Path(__file__).parent / "team_lead.md",
    )


if __name__ == "__main__":
    main()
