"""Maps GitHub Issue labels to agent names."""

LABEL_TO_AGENT = {
    "new":                    "pm",
    "pm-drafting":            "pm",
    "pm-revision":            "pm",
    "tl-pm-review":           "team_lead",
    "waiting-for-human":      None,  # paused — human must reply
    "approved-for-architect": "architect",
    "arch-drafting":          "architect",
    "tl-arch-review":         "team_lead",
    "in-dev":                 "backend",  # devops also polls this label
    "cr-review":              "code_reviewer",
    "in-qa":                  "qa",
    "tl-final-review":        "team_lead",
    "done":                   None,
}

STATUS_FLOW = [
    "new", "pm-drafting", "tl-pm-review", "pm-revision", "waiting-for-human",
    "approved-for-architect", "arch-drafting", "tl-arch-review",
    "in-dev", "cr-review", "in-qa", "tl-final-review", "done"
]
