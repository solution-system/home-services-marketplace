"""Shared values for service categories, statuses, and staff roles."""

CATEGORY_LABELS = {
    "plumbing": "Plumbing",
    "electrical": "Electrical",
    "cleaning": "Cleaning",
}

CATEGORIES = list(CATEGORY_LABELS.items())

STATUSES = (
    "New",
    "Assigned",
    "In Progress",
    "Completed",
    "Cancelled",
)

ROLES = ("admin", "provider")

MAX_FAILED_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 5
