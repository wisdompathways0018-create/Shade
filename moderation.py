import re

import discord
from discord.ext import commands

from config import get_server, save_server

# Hindi/Hinglish abusive-word variants supplied for Shade moderation.
# Text is normalised first so spacing, punctuation and common leetspeak are caught.
VULGAR_TERMS = {
    "bsdk", "bhosdike", "bhosdi ke", "bhosdikey", "bhosadike", "bhosda",
    "bhosdi", "bhosdiwala", "mc", "m c", "madarchod", "madar chod",
    "madarchuda", "madarchudi", "madarchut", "bc", "b c", "behenchod",
    "behen chod", "bhenchod", "bhen chod", "behen ch*d", "bhen ch*d",
    "chutiya", "chutiye", "chutia", "chuti", "chutiyapa", "chutiyapanti",
    "chutmarike", "chut mari ke", "gandu", "gaand", "gand", "gandfat",
    "gaandfat", "gand mara", "gaand mara", "gand marao", "randi", "rand",
    "randwa", "randi ka", "randi ke", "randi khana", "harami", "haraami",
    "haramzada", "haramzade", "haramkhor", "kamine", "kamina", "kaminey",
    "kaminapan", "kutte", "kutta", "kutti", "kutiya", "kutte ka", "kuttiya",
    "lodu", "lauda", "launda", "lund", "lundiya", "lund chus", "lund chusna",
    "chakka", "hijda", "hijre", "sala", "saala", "saale", "saali",
    "saala harami", "nalayak", "nikamma", "bakchod", "bakchodi", "bakchodi kar",
    "bakchodiya", "bkl", "b k l", "bklol", "bklolb.h.o.s.d.i.k.e",
    "b h o s d i k e", "bh0sdike", "bh0sd1ke", "bhosd1ke", "bhosd!ke",
    "bhosd@ke", "m@d@rch0d", "m4d4rch0d", "m4d4rchod", "chut1ya", "chut!ya",
    "g@ndu", "g4ndu", "l0du", "l@uda",
}

LEET_MAP = str.maketrans({
    "0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t",
    "@": "a", "$": "s", "!": "i", "*": "i",
})


def normalize(text: str) -> str:
    text = text.lower().translate(LEET_MAP)
    text = re.sub(r"[\u200b-\u200f\u2060\ufeff]", "", text)
    text = re.sub(r"[^a-z\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def is_vulgar(text: str) -> bool:
    normalized = normalize(text)
    compact = normalized.replace(" ", "")

    # Exact/phrase matching after normalisation.
    for term in VULGAR_TERMS:
        term_normalized = normalize(term)
        if not term_normalized:
            continue
        if " " in term_normalized:
            if term_normalized in normalized:
                return True
        elif re.search(rf"(?<![a-z]){re.escape(term_normalized)}(?![a-z])", normalized):
            return True

    # Catch terms deliberately written with spaces/punctuation between letters.
    compact_terms = {
        normalize(term).replace(" ", "")
        for term in VULGAR_TERMS
        if normalize(term).replace(" ", "")
    }
    return any(term in compact for term in compact_terms)


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
        if not message.content or not is_vulgar(message.content):
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
