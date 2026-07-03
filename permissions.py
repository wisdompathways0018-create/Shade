import discord


def is_leadership(member: discord.Member) -> bool:
    """Return True if the member is R5 or R6."""

    leadership_roles = {
        "R5",
        "R6"
    }

    return any(
        role.name in leadership_roles
        for role in member.roles
    )