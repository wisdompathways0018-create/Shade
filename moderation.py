import re
import secrets
import string

import discord
from discord import app_commands
from discord.ext import commands

from config import get_server, save_server

# Exact short abbreviations. These are matched as complete tokens only.
BANNED_ABBREVIATIONS = {
    "mc", "m c", "m.c", "bc", "b c", "b.c", "bkl", "b k l", "bklol"
}

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
    text = text.lower().translate(LEET_MAP)
    text = re.sub(r"[\u200b-\u200f\u2060\ufeff]", "", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _token_match(text: str, terms: set[str]) -> bool:
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
    if _token_match(text, OBFUSCATED_TERMS):
        return True

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
    if _token_match(text, BANNED_ABBREVIATIONS):
        return True
    if _token_match(text, BANNED_TERMS):
        return True
    return _obfuscated_token_match(text)


is_vulgar = contains_profanity


def _make_log_id() -> str:
    alphabet = string.ascii_uppercase + string.digits
    return f"LOG-{''.join(secrets.choice(alphabet) for _ in range(8))}-{''.join(secrets.choice(alphabet) for _ in range(4))}"


def _find_warning_channel(guild: discord.Guild, config: dict) -> discord.TextChannel | None:
    channel_id = config.get("warning_channel")
    if channel_id:
        channel = guild.get_channel(channel_id)
        if isinstance(channel, discord.TextChannel):
            return channel

    for channel in guild.text_channels:
        name = channel.name.lower()
        compact = re.sub(r"[^a-z0-9]+", " ", name).strip()
        if "warning" in compact and "log" in compact:
            return channel
    return None


def _format_original_message(message: discord.Message) -> str:
    content = (message.content or "").strip()
    attachments = "\n".join(attachment.url for attachment in message.attachments)

    if content and attachments:
        text = f"{content}\n{attachments}"
    elif content:
        text = content
    elif attachments:
        text = attachments
    else:
        text = "[No text content / attachment-only message]"

    text = text.replace("@everyone", "@ everyone").replace("@here", "@ here")
    if len(text) > 1000:
        text = text[:997] + "..."
    return text


async def _log_message(message: discord.Message):
    guild = message.guild
    if guild is None:
        return False

    config = get_server(guild.id)
    channel = _find_warning_channel(guild, config)
    if channel is None:
        return False

    log_id = _make_log_id()
    embed = discord.Embed(
        title="Message Logged",
        description="A message was removed by Shade's language filter and logged for leadership review.",
        color=discord.Color.orange(),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="Member", value=message.author.mention, inline=False)
    embed.add_field(name="Logged By", value=guild.me.mention if guild.me else "Shade", inline=False)
    embed.add_field(name="Channel", value=message.channel.mention, inline=False)
    embed.add_field(name="Message", value=_format_original_message(message), inline=False)
    embed.add_field(name="Log ID", value=f"`{log_id}`", inline=False)
    embed.set_footer(text="Shade • Moderation Log • No warning issued")

    try:
        await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
        return True
    except (discord.Forbidden, discord.HTTPException):
        return False


def setup(bot: commands.Bot):
    @bot.listen("on_message")
    async def moderation_listener(message: discord.Message):
        if message.guild is None or message.author.bot:
            return
        if not message.content or not contains_profanity(message.content):
            return

        # Remove the offending message, but DO NOT warn, timeout, or reply to the member.
        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            pass

        await _log_message(message)

    @bot.tree.command(name="warningchannel", description="Set the channel for Shade moderation logs")
    @app_commands.describe(channel="Select the warning log channel")
    async def warningchannel(interaction: discord.Interaction, channel: discord.TextChannel):
        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ This command can only be used in a server.", ephemeral=True
            )
            return

        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(
                "❌ You need **Manage Server** permission to set the warning channel.",
                ephemeral=True
            )
            return

        config = get_server(interaction.guild.id)
        config["warning_channel"] = channel.id
        save_server()
        await interaction.response.send_message(
            f"✅ Shade moderation logs will be sent to {channel.mention}",
            ephemeral=True
        )
