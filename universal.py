import asyncio
import random
import time

import discord
from discord import app_commands
from discord.ext import commands

from config import get_server, save_server


class TicketView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Open Ticket", emoji="🎫", style=discord.ButtonStyle.primary, custom_id="shade:ticket:open")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Server only.", ephemeral=True)
        config = get_server(interaction.guild.id)
        existing = discord.utils.find(
            lambda c: isinstance(c, discord.TextChannel) and c.topic == f"shade-ticket:{interaction.user.id}",
            interaction.guild.text_channels,
        )
        if existing:
            return await interaction.response.send_message(f"🎫 You already have {existing.mention}", ephemeral=True)

        category = None
        category_id = config.get("ticket_category")
        if category_id:
            found = interaction.guild.get_channel(category_id)
            if isinstance(found, discord.CategoryChannel):
                category = found

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
        }
        me = interaction.guild.me
        if me:
            overwrites[me] = discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True, read_message_history=True)
        for role in interaction.guild.roles:
            if role.name.lower() in {"staff", "moderator", "moderators", "admin", "admins"}:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)

        channel = await interaction.guild.create_text_channel(
            name=f"ticket-{interaction.user.name}"[:90],
            category=category,
            overwrites=overwrites,
            topic=f"shade-ticket:{interaction.user.id}",
            reason="Shade ticket opened",
        )
        embed = discord.Embed(title="🎫 Support Ticket", description="Please describe your issue. A staff member will help you soon.", color=discord.Color.blurple())
        await channel.send(content=interaction.user.mention, embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"✅ Ticket created: {channel.mention}", ephemeral=True)


class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="shade:ticket:close")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel) or not (channel.topic or "").startswith("shade-ticket:"):
            return await interaction.response.send_message("❌ This is not a Shade ticket.", ephemeral=True)
        await interaction.response.send_message("🔒 Closing ticket...", ephemeral=True)
        await asyncio.sleep(1)
        await channel.delete(reason=f"Shade ticket closed by {interaction.user}")


class RoleButtonView(discord.ui.View):
    def __init__(self, role_id: int):
        super().__init__(timeout=None)
        self.role_id = role_id

    @discord.ui.button(label="Get Role", emoji="🎭", style=discord.ButtonStyle.secondary, custom_id="shade:role")
    async def role_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Server only.", ephemeral=True)
        role = interaction.guild.get_role(self.role_id)
        if role is None:
            return await interaction.response.send_message("❌ That role no longer exists.", ephemeral=True)
        try:
            if role in interaction.user.roles:
                await interaction.user.remove_roles(role, reason="Shade role panel")
                text = f"➖ Removed {role.mention}"
            else:
                await interaction.user.add_roles(role, reason="Shade role panel")
                text = f"➕ Added {role.mention}"
            await interaction.response.send_message(text, ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Shade cannot manage that role. Move the Shade bot role above it.", ephemeral=True)


class GiveawayView(discord.ui.View):
    def __init__(self, giveaway_id: str):
        super().__init__(timeout=None)
        self.giveaway_id = giveaway_id

    @discord.ui.button(label="Enter Giveaway", emoji="🎉", style=discord.ButtonStyle.success, custom_id="shade:giveaway:enter")
    async def enter(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Server only.", ephemeral=True)
        config = get_server(interaction.guild.id)
        giveaways = config.setdefault("giveaways", {})
        data = giveaways.get(self.giveaway_id)
        if not data or data.get("ended"):
            return await interaction.response.send_message("❌ This giveaway has ended.", ephemeral=True)
        entries = data.setdefault("entries", [])
        uid = interaction.user.id
        if uid in entries:
            entries.remove(uid)
            save_server()
            return await interaction.response.send_message("➖ You left the giveaway.", ephemeral=True)
        entries.append(uid)
        save_server()
        await interaction.response.send_message("🎉 You are entered! Good luck!", ephemeral=True)


async def _finish_giveaway(bot: commands.Bot, guild_id: int, giveaway_id: str):
    config = get_server(guild_id)
    data = config.get("giveaways", {}).get(giveaway_id)
    if not data or data.get("ended"):
        return
    if time.time() < data.get("ends_at", 0):
        return
    data["ended"] = True
    entries = data.get("entries", [])
    guild = bot.get_guild(guild_id)
    channel = guild.get_channel(data.get("channel_id")) if guild else None
    winner = None
    if guild and entries:
        valid = [guild.get_member(uid) for uid in entries]
        valid = [m for m in valid if m and not m.bot]
        if valid:
            winner = random.choice(valid)
    save_server()
    if isinstance(channel, discord.TextChannel):
        if winner:
            await channel.send(f"🎉 **Giveaway ended!**\n🏆 Winner: {winner.mention}\n🎁 Prize: **{data['prize']}**")
        else:
            await channel.send(f"🎉 **Giveaway ended!** No valid entries. Prize: **{data['prize']}**")


async def _giveaway_loop(bot: commands.Bot):
    await bot.wait_until_ready()
    while not bot.is_closed():
        for guild in list(bot.guilds):
            config = get_server(guild.id)
            for giveaway_id in list(config.get("giveaways", {})):
                try:
                    await _finish_giveaway(bot, guild.id, giveaway_id)
                except Exception:
                    pass
        await asyncio.sleep(15)


def setup(bot: commands.Bot):
    bot.add_view(TicketView(bot))
    bot.add_view(CloseTicketView())

    @bot.tree.command(name="shade", description="Open Shade's universal server tools")
    async def shade(interaction: discord.Interaction):
        embed = discord.Embed(title="🌑 Shade • Server Assistant", color=discord.Color.dark_purple())
        embed.description = (
            "**Community**\n"
            "🎫 Tickets • 🎭 Roles • 👋 Welcome • 📋 Logs\n\n"
            "**Engagement**\n"
            "🎉 Giveaways • 📊 Polls • 💡 Suggestions\n\n"
            "**Safety**\n"
            "🛡️ AutoMod • 🔗 Invite protection • 💬 Spam protection\n\n"
            "**Gaming**\n"
            "❄️ Frost • ⚔️ Infinity Kingdom tools"
        )
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="ticketpanel", description="Post a Shade support ticket panel")
    @app_commands.describe(channel="Channel where the ticket panel should be posted")
    async def ticketpanel(interaction: discord.Interaction, channel: discord.TextChannel):
        if interaction.guild is None or not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You need Manage Server permission.", ephemeral=True)
        embed = discord.Embed(title="🎫 Need Help?", description="Click **Open Ticket** to create a private support channel.", color=discord.Color.blurple())
        await channel.send(embed=embed, view=TicketView(bot))
        await interaction.response.send_message(f"✅ Ticket panel posted in {channel.mention}", ephemeral=True)

    @bot.tree.command(name="ticketcategory", description="Set the category used for Shade tickets")
    @app_commands.describe(category="Ticket category")
    async def ticketcategory(interaction: discord.Interaction, category: discord.CategoryChannel):
        if interaction.guild is None or not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You need Manage Server permission.", ephemeral=True)
        config = get_server(interaction.guild.id)
        config["ticket_category"] = category.id
        save_server()
        await interaction.response.send_message(f"✅ Tickets will be created under {category.name}.", ephemeral=True)

    @bot.tree.command(name="welcomechannel", description="Set the welcome channel")
    @app_commands.describe(channel="Welcome channel")
    async def welcomechannel(interaction: discord.Interaction, channel: discord.TextChannel):
        if interaction.guild is None or not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You need Manage Server permission.", ephemeral=True)
        config = get_server(interaction.guild.id)
        config["welcome_channel"] = channel.id
        save_server()
        await interaction.response.send_message(f"✅ Welcome messages will be sent to {channel.mention}", ephemeral=True)

    @bot.tree.command(name="autorole", description="Set the role automatically given to new members")
    @app_commands.describe(role="Role to give new members")
    async def autorole(interaction: discord.Interaction, role: discord.Role):
        if interaction.guild is None or not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You need Manage Server permission.", ephemeral=True)
        config = get_server(interaction.guild.id)
        config["autorole"] = role.id
        save_server()
        await interaction.response.send_message(f"✅ New members will receive {role.mention}", ephemeral=True)

    @bot.event
    async def on_member_join(member: discord.Member):
        config = get_server(member.guild.id)
        role = member.guild.get_role(config.get("autorole")) if config.get("autorole") else None
        if role:
            try:
                await member.add_roles(role, reason="Shade autorole")
            except discord.Forbidden:
                pass
        channel = member.guild.get_channel(config.get("welcome_channel")) if config.get("welcome_channel") else None
        if isinstance(channel, discord.TextChannel):
            await channel.send(f"👋 Welcome {member.mention} to **{member.guild.name}**! Enjoy your stay.")

    @bot.tree.command(name="rolepanel", description="Create a button panel for a role")
    @app_commands.describe(channel="Channel for the panel", role="Role members can toggle")
    async def rolepanel(interaction: discord.Interaction, channel: discord.TextChannel, role: discord.Role):
        if interaction.guild is None or not interaction.user.guild_permissions.manage_roles:
            return await interaction.response.send_message("❌ You need Manage Roles permission.", ephemeral=True)
        if role >= interaction.guild.me.top_role:
            return await interaction.response.send_message("❌ Shade's role must be above that role.", ephemeral=True)
        embed = discord.Embed(title="🎭 Self Roles", description=f"Click the button to toggle {role.mention}.", color=discord.Color.blurple())
        await channel.send(embed=embed, view=RoleButtonView(role.id))
        await interaction.response.send_message("✅ Role panel posted.", ephemeral=True)

    @bot.tree.command(name="poll", description="Create a simple poll")
    @app_commands.describe(question="Poll question", options="Options separated by | (2-5 options)")
    async def poll(interaction: discord.Interaction, question: str, options: str):
        choices = [x.strip() for x in options.split("|") if x.strip()]
        if len(choices) < 2 or len(choices) > 5:
            return await interaction.response.send_message("❌ Provide 2-5 options separated with `|`.", ephemeral=True)
        numbers = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        description = "\n".join(f"{numbers[i]} **{choice}**" for i, choice in enumerate(choices))
        embed = discord.Embed(title="📊 Poll", description=f"**{question}**\n\n{description}", color=discord.Color.blurple())
        message = await interaction.channel.send(embed=embed)
        for emoji in numbers[:len(choices)]:
            await message.add_reaction(emoji)
        await interaction.response.send_message("✅ Poll created.", ephemeral=True)

    @bot.tree.command(name="giveaway", description="Start a giveaway")
    @app_commands.describe(minutes="Duration in minutes", prize="Prize description")
    async def giveaway(interaction: discord.Interaction, minutes: int, prize: str):
        if interaction.guild is None or not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You need Manage Server permission.", ephemeral=True)
        if minutes < 1 or minutes > 10080:
            return await interaction.response.send_message("❌ Duration must be 1 minute to 7 days.", ephemeral=True)
        config = get_server(interaction.guild.id)
        giveaways = config.setdefault("giveaways", {})
        giveaway_id = str(int(time.time() * 1000))
        giveaways[giveaway_id] = {"channel_id": interaction.channel.id, "prize": prize, "ends_at": time.time() + minutes * 60, "entries": [], "ended": False}
        save_server()
        embed = discord.Embed(title="🎉 GIVEAWAY", description=f"🎁 **Prize:** {prize}\n⏱️ **Ends:** <t:{int(time.time() + minutes * 60)}:R>\n\nClick below to enter!", color=discord.Color.gold())
        await interaction.response.send_message(embed=embed, view=GiveawayView(giveaway_id))

    @bot.tree.command(name="automod", description="Configure Shade AutoMod")
    @app_commands.describe(feature="profanity, spam, links, mentions, or caps", enabled="Enable or disable it")
    @app_commands.choices(feature=[
        app_commands.Choice(name="Profanity", value="profanity"),
        app_commands.Choice(name="Spam", value="spam"),
        app_commands.Choice(name="Links", value="links"),
        app_commands.Choice(name="Mentions", value="mentions"),
        app_commands.Choice(name="Caps", value="caps"),
    ])
    async def automod(interaction: discord.Interaction, feature: app_commands.Choice[str], enabled: bool):
        if interaction.guild is None or not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You need Manage Server permission.", ephemeral=True)
        config = get_server(interaction.guild.id)
        settings = config.setdefault("automod", {})
        settings[feature.value] = enabled
        save_server()
        await interaction.response.send_message(f"🛡️ AutoMod **{feature.name}**: **{'ON' if enabled else 'OFF'}**", ephemeral=True)

    @bot.listen("on_message")
    async def universal_automod(message: discord.Message):
        if message.guild is None or message.author.bot or not message.content:
            return
        config = get_server(message.guild.id)
        settings = config.get("automod", {})
        if settings.get("links") and ("discord.gg/" in message.content.lower() or "http://" in message.content.lower() or "https://" in message.content.lower()):
            try:
                await message.delete()
                await message.channel.send(f"🔗 {message.author.mention}, links are not allowed here.", delete_after=5)
            except discord.HTTPException:
                pass
            return
        if settings.get("mentions") and len(message.mentions) >= 5:
            try:
                await message.delete()
                await message.channel.send(f"📢 {message.author.mention}, excessive mentions are not allowed.", delete_after=5)
            except discord.HTTPException:
                pass
            return
        if settings.get("caps"):
            letters = [c for c in message.content if c.isalpha()]
            if len(letters) >= 12 and sum(c.isupper() for c in letters) / len(letters) >= 0.85:
                try:
                    await message.delete()
                    await message.channel.send(f"🔤 {message.author.mention}, please avoid excessive caps.", delete_after=5)
                except discord.HTTPException:
                    pass

    @bot.tree.command(name="userinfo", description="Show information about a member")
    @app_commands.describe(member="Member to inspect")
    async def userinfo(interaction: discord.Interaction, member: discord.Member):
        embed = discord.Embed(title=f"👤 {member.display_name}", color=member.color)
        embed.add_field(name="User", value=f"{member.mention}\n`{member.id}`", inline=False)
        embed.add_field(name="Joined", value=f"<t:{int(member.joined_at.timestamp())}:R>" if member.joined_at else "Unknown", inline=True)
        embed.add_field(name="Created", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
        roles = [r.mention for r in member.roles[1:]]
        embed.add_field(name="Roles", value=", ".join(roles[-10:]) if roles else "None", inline=False)
        if member.display_avatar:
            embed.set_thumbnail(url=member.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="serverinfo", description="Show server information")
    async def serverinfo(interaction: discord.Interaction):
        guild = interaction.guild
        if guild is None:
            return await interaction.response.send_message("❌ Server only.", ephemeral=True)
        embed = discord.Embed(title=f"🏠 {guild.name}", color=discord.Color.blurple())
        embed.add_field(name="Members", value=str(guild.member_count), inline=True)
        embed.add_field(name="Channels", value=str(len(guild.channels)), inline=True)
        embed.add_field(name="Roles", value=str(len(guild.roles)), inline=True)
        embed.add_field(name="Owner", value=f"<@{guild.owner_id}>", inline=True)
        embed.add_field(name="Created", value=f"<t:{int(guild.created_at.timestamp())}:D>", inline=True)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        await interaction.response.send_message(embed=embed)

    bot.loop.create_task(_giveaway_loop(bot))
