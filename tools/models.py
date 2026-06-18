# Model name constants (Bedrock inference profile IDs)
OPUS = "eu.anthropic.claude-opus-4-6-v1"
SONNET = "eu.anthropic.claude-sonnet-4-5-20250929-v1:0"
HAIKU = "eu.anthropic.claude-haiku-4-5-20251001-v1:0"

# Default models per agent role
AGENT_DEFAULTS = {
    "pm": OPUS,
    "team_lead": OPUS,
    "architect": SONNET,
    "backend": SONNET,
    "code_reviewer": SONNET,
    "qa": HAIKU,
    "devops": HAIKU,
}

# Minimum model floor — TL cannot assign below this
MODEL_TIER = {HAIKU: 0, SONNET: 1, OPUS: 2}
AGENT_MIN_MODEL = {
    "architect": SONNET,
    "code_reviewer": SONNET,
    "backend": HAIKU,
}


def get_tl_model_assignment(issue_number: int, agent_name: str) -> str | None:
    """Check issue comments for a Team Lead model assignment for this agent.

    Looks for a comment containing '[TEAM LEAD]' and 'Model assignments:',
    then parses out the line '- {agent_name}: {model}'.
    Enforces minimum model floor per agent.
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
                    min_model = AGENT_MIN_MODEL.get(agent_name)
                    if min_model and MODEL_TIER.get(model, 0) < MODEL_TIER.get(min_model, 0):
                        return min_model
                    return model
    return None
