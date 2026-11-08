"""Single place for the status rules shared by routes and templates."""

# Providers may only move a job forward one step at a time.
PROVIDER_TRANSITIONS = {
    "Assigned": "In Progress",
    "In Progress": "Completed",
}

PROVIDER_ACTION_LABELS = {
    "In Progress": "Start work",
    "Completed": "Mark completed",
}

PROVIDER_TRANSITION_MESSAGES = {
    "In Progress": "The service provider has started work on your request.",
    "Completed": "The work is complete. Thank you for choosing Goodhand.",
}


def next_provider_status(current_status):
    """Return the only status a provider may move this job to, if any."""
    return PROVIDER_TRANSITIONS.get(current_status)
