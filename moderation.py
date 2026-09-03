import re

import discord
from discord.ext import commands

from config import get_server, save_server


# Common Hindi/Hinglish profanity patterns.
# Matching is performed after normalising case, punctuation and common leetspeak.
VULGAR_PATTERNS = [
    r"\bmadarchod\b", r"\bmc\b", r"\bmadarchod\b",
    r"\bbehenchod\b", r"\bbhenchod\b", r"\bbc\b",
    r"\bchutiya\b", r"\bchutiy[ae]\b", r"\bchut\b",
    r"\bgandu\b", r"\bgandua\b", r"\bbhosd[aiy]k?\b",
    r"\bbhosdi\b", r"\bbhosdike\b", r"\brand[iy]\b",
    r"\bharamzada\b", r"\bharamzade\b", r"\bkamina\b",
    r"\bkamini\b", r"\bkutte?\b", r"\bsuar\b",
    r"\blavde?\b", r"\blund\b", r"\bgaand\b", r"\bchodu\b",
]

LEET_MAP = str.maketrans({
    "0": "o", "1": "i", "3": "e", "4": "a", "5": "s",
    "7": "t", "@": "a", "$": "s",
})


def normalize(text: str) -> str:
    text = text.lower().translate(LEET_MAP)
    text = re.sub(r"[\u200b-\u200f\u2060\ufeff]", "", text)
    text = re.sub(r"[^a-z\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def is_vulgar(text: str) -> bool:
    normalized = normalize(text)
    compact = normalized.replace(" ", "")
    for pattern in VULGAR_PATTERNS:
        if re.search(pattern, normalized):
            return True
    # Catch profanity split by spaces/punctuation, while keeping the list explicit.
    compact_patterns = [
        "madarchod", "madar chod", "behenchod", "bhenchod",
        "chutiya", "gandu", "bhosdike", "bhosdi", "haramzada",
        "haramzade", "lavda", "lavde", "lund", "gaand", "chodu",
    ]
    return any(p.replace(" ", "") in compact for p in compact_patterns)


async def _warn(member: discord.Member, guild: discord.Guild, channel: discord.abc.Messageable):
    config = get_server(guild.id)
    warnings = config.setdefault("moderation_warnings", {})
    user_id = str(member.id)
    warnings[user_id] = int(warnings.get(user_id, 0)) + 1
    save_server()
    return warnings[user_id]


def setup(bot: commands.Bot):
    @bot.listen("on_message")
    async def moderation_listener(message: discord.Message):
        if message.guild is None or message.author.bot:
            return
        if not message.content or not is_vulgar(message.content):
            return

        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound):
            return
        except discord.HTTPException:
            return

        warning_count = await _warn(message.author, message.guild, message.channel)

        try:
            await message.channel.send(
                f"⚠️ {message.author.mention}, vulgar/abusive language is not allowed here. "
                f"**Warning #{warning_count}** recorded.",
                delete_after=8,
            )
        except (discord.Forbidden, discord.HTTPException):
            pass
