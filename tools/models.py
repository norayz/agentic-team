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
