"""Maps GitHub Issue labels to agent names."""

LABEL_TO_AGENT = {
    "new":                    "pm",
    "pm-drafting":            "pm",
    "tl-pm-review":           "team_lead",
    "waiting-for-human":      None,  # paused
    "approved-for-architect": "architect",
    "arch-drafting":          "architect",
    "tl-arch-review":         "team_lead",
    "in-dev":                 "backend",  # devops also picks this up
    "cr-review":              "code_reviewer",
    "in-qa":                  "qa",
    "in-devops":              "devops",
    "tl-final-review":        "team_lead",
    "done":                   None,
}

STATUS_FLOW = [
    "new", "pm-drafting", "tl-pm-review", "waiting-for-human",
    "approved-for-architect", "arch-drafting", "tl-arch-review",
    "in-dev", "cr-review", "in-qa", "tl-final-review", "done"
]
