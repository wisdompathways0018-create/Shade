"""Shade owner identity and owner-only helpers."""

OWNER_USER_ID = 1463254383398490325
OWNER_NAME = "Shade Owner"
BIRTHDAY_DATE = "10-02"


def is_owner(user) -> bool:
    """Return True when the Discord user is Shade's owner."""
    return getattr(user, "id", None) == OWNER_USER_ID
