# Model name constants
OPUS = "claude-opus-4-8"
SONNET = "claude-sonnet-4-6"
HAIKU = "claude-haiku-4-5-20251001"

# Default models per agent role
AGENT_DEFAULTS = {
    "pm": OPUS,
    "team_lead": OPUS,
    "architect": SONNET,
    "backend": HAIKU,
    "code_reviewer": SONNET,
    "qa": HAIKU,
    "devops": HAIKU,
}


def get_tl_model_assignment(issue_number: int, agent_name: str) -> str | None:
    """Check issue comments for a Team Lead model assignment for this agent.

    Looks for a comment containing '[TEAM LEAD]' and 'Model assignments:',
    then parses out the line '- {agent_name}: {model}'.
    Returns the model string if found, None otherwise.
    """
    from tools.github_issues import get_comments

    comments = get_comments(issue_number)
    for comment in reversed(comments):
        body = comment.get("body", "")
        if "[TEAM LEAD]" not in body or "Model assignments:" not in body:
            continue
        for line in body.splitlines():
            line = line.strip()
            prefix = f"- {agent_name}:"
            if line.startswith(prefix):
                model = line[len(prefix):].strip()
                if model:
                    return model
    return None
