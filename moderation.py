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

    # Join only runs of 2-9 single-letter tokens. This catches deliberate
    # forms such as 'm c'/'b c'/'b h o s d i k e' while avoiding
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


def _make_warning_id() -> str:
    """Create a short ticket-style warning ID such as WRN-MTK8CX96-NV3K."""
    alphabet = string.ascii_uppercase + string.digits
    return f"WRN-{''.join(secrets.choice(alphabet) for _ in range(8))}-{''.join(secrets.choice(alphabet) for _ in range(4))}"


def _find_warning_channel(guild: discord.Guild, config: dict) -> discord.TextChannel | None:
    """Use the configured log channel, otherwise auto-detect #warning-logs."""
    channel_id = config.get("warning_channel")
    if channel_id:
        channel = guild.get_channel(channel_id)
        if isinstance(channel, discord.TextChannel):
            return channel

    for channel in guild.text_channels:
        if channel.name.lower() in {"warning-logs", "warning_logs", "warninglogs"}:
            return channel

    return None


async def _warn(member: discord.Member, guild: discord.Guild):
    config = get_server(guild.id)
    warnings = config.setdefault("moderation_warnings", {})
    user_id = str(member.id)
    warnings[user_id] = int(warnings.get(user_id, 0)) + 1
    warning_count = warnings[user_id]

    warning_id = _make_warning_id()
    tickets = config.setdefault("moderation_warning_tickets", [])
    tickets.append({
        "warning_id": warning_id,
        "user_id": member.id,
        "warning_count": warning_count
    })

    # Keep the persistent log from growing without bound.
    if len(tickets) > 1000:
        del tickets[:-1000]

    save_server()
    return warning_count, warning_id


async def _send_warning_ticket(message: discord.Message, warning_count: int, warning_id: str):
    guild = message.guild
    if guild is None:
        return False

    config = get_server(guild.id)
    channel = _find_warning_channel(guild, config)

    # If #warning-logs cannot be found, use the command channel as a guaranteed
    # fallback so the warning ticket is never silently lost.
    if channel is None:
        channel = message.channel

    embed = discord.Embed(
        title="⚠️ Member Warned",
        color=discord.Color.red(),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(name="Member", value=message.author.mention, inline=False)
    embed.add_field(name="Warned By", value=f"{guild.me.mention if guild.me else 'Shade'}", inline=False)
    embed.add_field(name="Reason", value="Vulgar/abusive language detected by Shade.", inline=False)
    embed.add_field(name="Duration", value="No timeout (warning only)", inline=False)
    embed.add_field(name="Messaging", value="Allowed (warning only)", inline=False)
    embed.add_field(name="Warning Count", value=str(warning_count), inline=False)
    embed.add_field(name="Command Channel", value=message.channel.mention, inline=False)
    embed.add_field(name="Warning ID", value=f"`{warning_id}`", inline=False)
    embed.set_footer(text="Shade Moderation • Warning Ticket")

    try:
        await channel.send(embed=embed)
        return True
    except (discord.Forbidden, discord.HTTPException):
        # If the configured #warning-logs channel is inaccessible, try the
        # original channel instead of losing the ticket completely.
        if channel.id != message.channel.id:
            try:
                await message.channel.send(embed=embed)
                return True
            except (discord.Forbidden, discord.HTTPException):
                pass
        return False


def setup(bot: commands.Bot):
    @bot.listen("on_message")
    async def moderation_listener(message: discord.Message):
        if message.guild is None or message.author.bot:
            return
        if not message.content or not contains_profanity(message.content):
            return

        # Do not stop moderation if message deletion fails because Shade lacks
        # Manage Messages. The warning ticket must still be recorded/logged.
        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            pass

        warning_count, warning_id = await _warn(message.author, message.guild)

        # Log a ticket-style warning in #warning-logs (or the configured channel).
        ticket_sent = await _send_warning_ticket(message, warning_count, warning_id)

        try:
            reply = (
                f"⚠️ {message.author.mention}, vulgar/abusive language is not allowed here. "
                f"**Warning #{warning_count}** recorded. Warning ID: `{warning_id}`"
            )
            if not ticket_sent:
                reply += "\n⚠️ Warning log could not be posted. Please check Shade's channel permissions."
            await message.channel.send(reply, delete_after=8)
        except (discord.Forbidden, discord.HTTPException):
            pass

    @bot.tree.command(name="warningchannel", description="Set the channel for Shade warning tickets")
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
            f"✅ Shade warning tickets will be sent to {channel.mention}",
            ephemeral=True
        )
