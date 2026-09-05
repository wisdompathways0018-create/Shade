import asyncio
import random
import time

import discord
from discord import app_commands
from discord.ext import commands

from config import get_server, save_server


XP_COOLDOWN = 60


class SuggestionView(discord.ui.View):
    def __init__(self, suggestion_id: str):
        super().__init__(timeout=None)
        self.suggestion_id = suggestion_id

    async def _update(self, interaction: discord.Interaction, status: str, emoji: str):
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Server only.", ephemeral=True)
        if not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You need Manage Server permission.", ephemeral=True)
        config = get_server(interaction.guild.id)
        data = config.get("suggestions", {}).get(self.suggestion_id)
        if not data:
            return await interaction.response.send_message("❌ Suggestion not found.", ephemeral=True)
        data["status"] = status
        data["reviewed_by"] = interaction.user.id
        save_server()
        embed = interaction.message.embeds[0] if interaction.message.embeds else discord.Embed(title="💡 Suggestion")
        embed.color = discord.Color.green() if status == "Approved" else discord.Color.red()
        embed.set_footer(text=f"Shade • {emoji} {status} by {interaction.user.display_name}")
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message(f"{emoji} Suggestion marked **{status}**.", ephemeral=True)

    @discord.ui.button(label="Approve", emoji="✅", style=discord.ButtonStyle.success, custom_id="shade:suggestion:approve")
    async def approve(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._update(interaction, "Approved", "✅")

    @discord.ui.button(label="Reject", emoji="❌", style=discord.ButtonStyle.danger, custom_id="shade:suggestion:reject")
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._update(interaction, "Rejected", "❌")


class StarboardListener:
    def __init__(self, bot: commands.Bot):
        self.bot = bot


async def _birthday_loop(bot: commands.Bot):
    await bot.wait_until_ready()
    while not bot.is_closed():
        today = time.strftime("%m-%d", time.gmtime())
        for guild in list(bot.guilds):
            config = get_server(guild.id)
            birthday_channel_id = config.get("birthday_channel")
            channel = guild.get_channel(birthday_channel_id) if birthday_channel_id else None
            if not isinstance(channel, discord.TextChannel):
                continue
            birthdays = config.get("birthdays", {})
            announced = config.setdefault("birthday_announced", {})
            for uid, date in birthdays.items():
                if date != today or announced.get(uid) == today:
                    continue
                member = guild.get_member(int(uid))
                if member:
                    await channel.send(f"🎂 Happy Birthday {member.mention}! 🎉 Have an amazing day!")
                    announced[uid] = today
            save_server()
        await asyncio.sleep(3600)


def setup(bot: commands.Bot):
    bot.add_view(SuggestionView("persistent"))

    @bot.tree.command(name="level", description="Show a member's Shade level")
    @app_commands.describe(member="Member to check")
    async def level(interaction: discord.Interaction, member: discord.Member | None = None):
        member = member or interaction.user
        config = get_server(interaction.guild.id)
        data = config.get("levels", {}).get(str(member.id), {})
        xp = int(data.get("xp", 0))
        lvl = int(data.get("level", 0))
        next_xp = (lvl + 1) * 100
        embed = discord.Embed(title="📈 Shade Level", color=discord.Color.blurple())
        embed.add_field(name="Member", value=member.mention, inline=False)
        embed.add_field(name="Level", value=str(lvl), inline=True)
        embed.add_field(name="XP", value=f"{xp}/{next_xp}", inline=True)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="leaderboard", description="Show the server XP leaderboard")
    async def leaderboard(interaction: discord.Interaction):
        config = get_server(interaction.guild.id)
        levels = config.get("levels", {})
        rows = []
        for uid, data in levels.items():
            member = interaction.guild.get_member(int(uid))
            if member and not member.bot:
                rows.append((int(data.get("xp", 0)), member))
        rows.sort(key=lambda x: x[0], reverse=True)
        lines = []
        for i, (xp, member) in enumerate(rows[:10], 1):
            lvl = int(config["levels"][str(member.id)].get("level", 0))
            lines.append(f"**{i}.** {member.display_name} — Level **{lvl}** • {xp} XP")
        embed = discord.Embed(title="🏆 Shade XP Leaderboard", description="\n".join(lines) or "No XP recorded yet.", color=discord.Color.gold())
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="levelchannel", description="Set the channel for level-up announcements")
    @app_commands.describe(channel="Level-up announcement channel")
    async def levelchannel(interaction: discord.Interaction, channel: discord.TextChannel):
        if interaction.guild is None or not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You need Manage Server permission.", ephemeral=True)
        config = get_server(interaction.guild.id)
        config["level_channel"] = channel.id
        save_server()
        await interaction.response.send_message(f"✅ Level-up announcements will use {channel.mention}", ephemeral=True)

    @bot.tree.command(name="starboardchannel", description="Set the Starboard channel")
    @app_commands.describe(channel="Channel for popular messages")
    async def starboardchannel(interaction: discord.Interaction, channel: discord.TextChannel):
        if interaction.guild is None or not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You need Manage Server permission.", ephemeral=True)
        config = get_server(interaction.guild.id)
        config["starboard_channel"] = channel.id
        config.setdefault("starboard", {})
        save_server()
        await interaction.response.send_message(f"⭐ Starboard set to {channel.mention}", ephemeral=True)

    @bot.tree.command(name="starboardthreshold", description="Set how many ⭐ reactions a message needs")
    @app_commands.describe(count="Stars required (1-25)")
    async def starboardthreshold(interaction: discord.Interaction, count: int):
        if interaction.guild is None or not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You need Manage Server permission.", ephemeral=True)
        if not 1 <= count <= 25:
            return await interaction.response.send_message("❌ Choose 1-25.", ephemeral=True)
        config = get_server(interaction.guild.id)
        config["starboard_threshold"] = count
        save_server()
        await interaction.response.send_message(f"⭐ Starboard threshold: **{count}**", ephemeral=True)

    @bot.tree.command(name="suggest", description="Submit a server suggestion")
    @app_commands.describe(text="Your suggestion")
    async def suggest(interaction: discord.Interaction, text: str):
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Server only.", ephemeral=True)
        text = text.strip()
        if not text or len(text) > 1000:
            return await interaction.response.send_message("❌ Suggestion must be 1-1000 characters.", ephemeral=True)
        config = get_server(interaction.guild.id)
        suggestions = config.setdefault("suggestions", {})
        sid = str(int(time.time() * 1000))
        suggestions[sid] = {"author_id": interaction.user.id, "text": text, "status": "Pending"}
        channel_id = config.get("suggestion_channel")
        channel = interaction.guild.get_channel(channel_id) if channel_id else interaction.channel
        embed = discord.Embed(title="💡 New Suggestion", description=text, color=discord.Color.blurple())
        embed.add_field(name="Submitted by", value=interaction.user.mention, inline=True)
        embed.add_field(name="Status", value="🟡 Pending", inline=True)
        if isinstance(channel, discord.TextChannel):
            await channel.send(embed=embed, view=SuggestionView(sid))
        save_server()
        await interaction.response.send_message("✅ Suggestion submitted.", ephemeral=True)

    @bot.tree.command(name="suggestionchannel", description="Set the suggestion channel")
    @app_commands.describe(channel="Suggestion channel")
    async def suggestionchannel(interaction: discord.Interaction, channel: discord.TextChannel):
        if interaction.guild is None or not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You need Manage Server permission.", ephemeral=True)
        config = get_server(interaction.guild.id)
        config["suggestion_channel"] = channel.id
        save_server()
        await interaction.response.send_message(f"✅ Suggestions will be posted in {channel.mention}", ephemeral=True)

    @bot.tree.command(name="birthday", description="Set or clear your birthday")
    @app_commands.describe(date="Birthday as MM-DD, or leave blank to clear")
    async def birthday(interaction: discord.Interaction, date: str | None = None):
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Server only.", ephemeral=True)
        config = get_server(interaction.guild.id)
        birthdays = config.setdefault("birthdays", {})
        if date is None:
            birthdays.pop(str(interaction.user.id), None)
            save_server()
            return await interaction.response.send_message("🎂 Birthday removed.", ephemeral=True)
        try:
            month, day = map(int, date.split("-"))
            if not (1 <= month <= 12 and 1 <= day <= 31):
                raise ValueError
            normalized = f"{month:02d}-{day:02d}"
        except ValueError:
            return await interaction.response.send_message("❌ Use **MM-DD**, for example `09-03`.", ephemeral=True)
        birthdays[str(interaction.user.id)] = normalized
        save_server()
        await interaction.response.send_message(f"🎂 Birthday saved as **{normalized}**.", ephemeral=True)

    @bot.tree.command(name="birthdaychannel", description="Set the birthday announcement channel")
    @app_commands.describe(channel="Birthday channel")
    async def birthdaychannel(interaction: discord.Interaction, channel: discord.TextChannel):
        if interaction.guild is None or not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You need Manage Server permission.", ephemeral=True)
        config = get_server(interaction.guild.id)
        config["birthday_channel"] = channel.id
        save_server()
        await interaction.response.send_message(f"✅ Birthday announcements will use {channel.mention}", ephemeral=True)

    @bot.tree.command(name="afk", description="Set an AFK status")
    @app_commands.describe(reason="Why you are AFK")
    async def afk(interaction: discord.Interaction, reason: str = "AFK"):
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Server only.", ephemeral=True)
        config = get_server(interaction.guild.id)
        afks = config.setdefault("afk", {})
        afks[str(interaction.user.id)] = {"reason": reason[:200], "since": time.time()}
        save_server()
        await interaction.response.send_message(f"💤 {interaction.user.mention} is now AFK: **{reason[:200]}**")

    @bot.listen("on_message")
    async def community_message_listener(message: discord.Message):
        if message.guild is None or message.author.bot:
            return
        config = get_server(message.guild.id)
        afks = config.setdefault("afk", {})
        author_key = str(message.author.id)
        if author_key in afks:
            afks.pop(author_key, None)
            await message.channel.send(f"👋 Welcome back {message.author.mention}! Your AFK has been removed.", delete_after=6)
        for mentioned in message.mentions[:5]:
            data = afks.get(str(mentioned.id))
            if data:
                await message.channel.send(f"💤 {mentioned.display_name} is AFK: **{data.get('reason', 'AFK')}**", delete_after=8)

        now = time.time()
        levels = config.setdefault("levels", {})
        data = levels.setdefault(author_key, {"xp": 0, "level": 0, "last_xp": 0})
        if now - float(data.get("last_xp", 0)) >= XP_COOLDOWN:
            gain = random.randint(8, 15)
            data["xp"] = int(data.get("xp", 0)) + gain
            old_level = int(data.get("level", 0))
            new_level = int(data["xp"] // 100)
            data["level"] = new_level
            data["last_xp"] = now
            if new_level > old_level:
                channel_id = config.get("level_channel")
                channel = message.guild.get_channel(channel_id) if channel_id else message.channel
                if isinstance(channel, discord.TextChannel):
                    await channel.send(f"🎉 Congratulations {message.author.display_name}! You reached **Level {new_level}**!")
            save_server()

    @bot.listen("on_raw_reaction_add")
    async def starboard_listener(payload: discord.RawReactionActionEvent):
        if payload.guild_id is None or str(payload.emoji) != "⭐" or (bot.user and payload.user_id == bot.user.id):
            return
        guild = bot.get_guild(payload.guild_id)
        if guild is None:
            return
        config = get_server(guild.id)
        channel_id = config.get("starboard_channel")
        if not channel_id:
            return
        threshold = int(config.get("starboard_threshold", 5))
        source = guild.get_channel(payload.channel_id)
        starboard = guild.get_channel(channel_id)
        if not isinstance(source, discord.TextChannel) or not isinstance(starboard, discord.TextChannel):
            return
        try:
            message = await source.fetch_message(payload.message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return
        reaction = next((r for r in message.reactions if str(r.emoji) == "⭐"), None)
        if reaction is None or reaction.count < threshold:
            return
        records = config.setdefault("starboard", {})
        key = str(message.id)
        if key in records:
            try:
                posted = await starboard.fetch_message(records[key])
                await posted.edit(content=f"⭐ **{reaction.count}** • {message.author.mention}\n{message.content[:1800]}")
            except discord.HTTPException:
                pass
            return
        embed = discord.Embed(description=message.content[:4000] or "[Attachment / embed message]", color=discord.Color.gold(), timestamp=message.created_at)
        embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
        if message.attachments:
            embed.set_image(url=message.attachments[0].url)
        try:
            posted = await starboard.send(content=f"⭐ **{reaction.count}** • {message.author.mention}", embed=embed)
            records[key] = posted.id
            save_server()
        except discord.HTTPException:
            pass

    bot.loop.create_task(_birthday_loop(bot))
