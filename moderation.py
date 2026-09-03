import re

import discord
from discord.ext import commands

from config import get_server, save_server

# Exact short abbreviations. These are matched as complete tokens only.
BANNED_ABBREVIATIONS = {
    "mc", "m c", "m.c", "bc", "b c", "b.c", "bkl", "b k l", "bklol"
}

# Longer terms are also matched as complete words/phrases after normalisation.
BANNED_TERMS = {
    "bsdk", "bhosdike", "bhosdi ke", "bhosdikey", "bhosadike", "bhosda",
    "bhosdi", "bhosdiwala", "madarchod", "madar chod", "madarchuda",
    "madarchudi", "madarchut", "behenchod", "behen chod", "bhenchod",
    "bhen chod", "behen ch d", "bhen ch d", "chutiya", "chutiye", "chutia",
    "chuti", "chutiyapa", "chutiyapanti", "chutmarike", "chut mari ke",
    "gandu", "gaand", "gand", "gandfat", "gaandfat", "gand mara",
    "gaand mara", "gand marao", "randi", "rand", "randwa", "randi ka",
    "randi ke", "randi khana", "harami", "haraami", "haramzada", "haramzade",
    "haramkhor", "kamine", "kamina", "kaminey", "kaminapan", "kutte", "kutta",
    "kutti", "kutiya", "kutte ka", "kuttiya", "lodu", "lauda", "launda", "lund",
    "lundiya", "lund chus", "lund chusna", "chakka", "hijda", "hijre", "sala",
    "saala", "saale", "saali", "saala harami", "nalayak", "nikamma", "bakchod",
    "bakchodi", "bakchodi kar", "bakchodiya"
}

# Common obfuscations supplied by the user. These are normalised before matching.
OBFUSCATED_TERMS = {
    "bklolb.h.o.s.d.i.k.e", "b h o s d i k e", "bh0sdike", "bh0sd1ke",
    "bhosd1ke", "bhosd!ke", "bhosd@ke", "m@d@rch0d", "m4d4rch0d",
    "m4d4rchod", "chut1ya", "chut!ya", "g@ndu", "g4ndu", "l0du", "l@uda"
}

LEET_MAP = str.maketrans({
    "0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t",
    "@": "a", "$": "s", "!": "i", "*": "i"
})


def normalize_text(text: str) -> str:
    """Normalise case, leetspeak, zero-width characters and punctuation."""
    text = text.lower().translate(LEET_MAP)
    text = re.sub(r"[\u200b-\u200f\u2060\ufeff]", "", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _token_match(text: str, terms: set[str]) -> bool:
    """Match short/normal terms as whole tokens or complete phrases."""
    words = text.split()
    word_set = set(words)

    for term in terms:
        normal = normalize_text(term)
        if not normal:
            continue
        if " " in normal:
            if normal in text:
                return True
        elif normal in word_set:
            return True
    return False


def _obfuscated_token_match(text: str) -> bool:
    """Catch deliberately separated/obfuscated forms without substring matching normal words."""
    if _token_match(text, OBFUSCATED_TERMS):
        return True

    # Only join runs of 2-4 single-letter alphabetic tokens. This catches
    # deliberate forms such as 'm c'/'b c'/'b h o s d i k e' while avoiding
    # substring matching inside ordinary English words.
    words = text.split()
    for size in (2, 3, 4, 5, 6, 7, 8, 9):
        for i in range(len(words) - size + 1):
            chunk = words[i:i + size]
            if all(len(word) == 1 for word in chunk):
                joined = "".join(chunk)
                if joined in {"mc", "bc", "bkl", "bsdk", "bhosdike"}:
                    return True
    return False


def contains_profanity(message: str) -> bool:
    text = normalize_text(message)

    if not text:
        return False

    # Critical: mc/bc and other short terms are exact-token matches.
    if _token_match(text, BANNED_ABBREVIATIONS):
        return True

    if _token_match(text, BANNED_TERMS):
        return True

    return _obfuscated_token_match(text)


# Backwards-compatible name used by older code.
is_vulgar = contains_profanity


async def _warn(member: discord.Member, guild: discord.Guild):
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
        if not message.content or not contains_profanity(message.content):
            return

        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            return

        warning_count = await _warn(message.author, message.guild)

        try:
            await message.channel.send(
                f"⚠️ {message.author.mention}, vulgar/abusive language is not allowed here. "
                f"**Warning #{warning_count}** recorded.",
                delete_after=8,
            )
        except (discord.Forbidden, discord.HTTPException):
            pass
