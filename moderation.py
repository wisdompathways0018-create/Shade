import re
import secrets
import string

import discord
from discord import app_commands
from discord.ext import commands

from config import get_server, save_server

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

URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)


def normalize_text(text: str) -> str:
    text = text.lower().translate(LEET_MAP)
    text = re.sub(r"[\u200b-\u200f\u2060\ufeff]", "", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _text_for_moderation(message: str) -> str:
    # Never inspect URL domains/paths for profanity. A GIF/image/video URL is
    # not a user's language and must not be capable of triggering the filter.
    without_urls = URL_RE.sub(" ", message or "")
    return normalize_text(without_urls)


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
    text = _text_for_moderation(message)
    if not text:
        return False
    return (
        _token_match(text, BANNED_ABBREVIATIONS)
        or _token_match(text, BANNED_TERMS)
        or _obfuscated_token_match(text)
    )


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
        compact = re.sub(r"[^a-z0-9]+", " ", channel.name.lower()).strip()
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
        timestamp=discord.utils.utcnow(),
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


async def _log_invite_created(invite: discord.Invite):
    guild = invite.guild
    if guild is None:
        return False
    config = get_server(guild.id)
    channel = _find_warning_channel(guild, config)
    if channel is None:
        return False

    inviter = invite.inviter
    inviter_text = inviter.mention if inviter else "Unknown / unavailable"
    inviter_id = f"`{inviter.id}`" if inviter else "Unknown"
    channel_text = invite.channel.mention if isinstance(invite.channel, discord.abc.GuildChannel) else "Unknown / unavailable"
    max_age = f"{invite.max_age // 3600}h" if invite.max_age else "Never"
    max_uses = str(invite.max_uses) if invite.max_uses else "Unlimited"

    embed = discord.Embed(
        title="🔗 Invite Created",
        description="A new Discord invite was created in this server.",
        color=discord.Color.blue(),
        timestamp=discord.utils.utcnow(),
    )
    embed.add_field(name="Created By", value=inviter_text, inline=True)
    embed.add_field(name="User ID", value=inviter_id, inline=True)
    embed.add_field(name="Channel", value=channel_text, inline=True)
    embed.add_field(name="Invite", value=f"`{invite.url}`", inline=False)
    embed.add_field(name="Expires", value=max_age, inline=True)
    embed.add_field(name="Max Uses", value=max_uses, inline=True)
    embed.set_footer(text="Shade • Moderation Log • Invite Creation")

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
        config = get_server(message.guild.id)
        # Moderation can be disabled per server without removing the feature.
        if config.get("moderation_enabled", True) is False:
            return
        # Attachment-only posts and URL-only posts are never moderation text.
        if not message.content or not _text_for_moderation(message.content):
            return
        if not contains_profanity(message.content):
            return
        try:
            await message.delete()
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            pass
        await _log_message(message)

    @bot.listen("on_invite_create")
    async def invite_creation_listener(invite: discord.Invite):
        # Invite logging remains active even when the language filter is disabled.
        await _log_invite_created(invite)

    @bot.tree.command(name="warningchannel", description="Set the channel for Shade moderation logs")
    @app_commands.describe(channel="Select the warning log channel")
    async def warningchannel(interaction: discord.Interaction, channel: discord.TextChannel):
        if interaction.guild is None:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need **Manage Server** permission to set the warning channel.", ephemeral=True)
            return
        config = get_server(interaction.guild.id)
        config["warning_channel"] = channel.id
        save_server()
        await interaction.response.send_message(f"✅ Shade moderation logs will be sent to {channel.mention}", ephemeral=True)

    @bot.tree.command(name="moderation", description="Enable or disable Shade's automatic language moderation")
    @app_commands.describe(action="Choose whether Shade should automatically filter messages")
    @app_commands.choices(action=[
        app_commands.Choice(name="Enable", value="enable"),
        app_commands.Choice(name="Disable", value="disable"),
    ])
    async def moderation(interaction: discord.Interaction, action: app_commands.Choice[str]):
        if interaction.guild is None:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ You need **Manage Server** permission to change Shade moderation.", ephemeral=True)
            return

        config = get_server(interaction.guild.id)
        enabled = action.value == "enable"
        config["moderation_enabled"] = enabled
        save_server()

        if enabled:
            await interaction.response.send_message("✅ Shade's automatic language moderation is now **enabled**.")
        else:
            await interaction.response.send_message("🛑 Shade's automatic language moderation is now **disabled**. Other Shade features, including invite logging, will continue working.")
