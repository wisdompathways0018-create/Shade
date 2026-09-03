import discord
from discord import app_commands
from discord.ext import commands


def setup(bot: commands.Bot):
    @bot.tree.command(name="userinfo", description="Show detailed information about a member")
    @app_commands.describe(member="Member to inspect")
    async def userinfo(interaction: discord.Interaction, member: discord.Member | None = None):
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Server only.", ephemeral=True)
        member = member or interaction.user
        roles = [r.mention for r in member.roles[1:]]
        embed = discord.Embed(title=f"👤 User Information • {member.display_name}", color=discord.Color.blurple())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Username", value=str(member), inline=True)
        embed.add_field(name="User ID", value=str(member.id), inline=True)
        embed.add_field(name="Bot", value="Yes" if member.bot else "No", inline=True)
        embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:F>", inline=False)
        embed.add_field(name="Joined Server", value=f"<t:{int(member.joined_at.timestamp())}:F>" if member.joined_at else "Unknown", inline=False)
        embed.add_field(name="Top Role", value=member.top_role.mention, inline=True)
        embed.add_field(name="Roles", value=" ".join(roles[-15:]) if roles else "None", inline=False)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="serverinfo", description="Show detailed information about this server")
    async def serverinfo(interaction: discord.Interaction):
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Server only.", ephemeral=True)
        guild = interaction.guild
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        bots = sum(1 for m in guild.members if m.bot)
        humans = max(0, guild.member_count - bots)
        embed = discord.Embed(title=f"🏠 Server Information • {guild.name}", color=discord.Color.dark_purple())
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="Server ID", value=str(guild.id), inline=True)
        embed.add_field(name="Owner", value=f"<@{guild.owner_id}>" if guild.owner_id else "Unknown", inline=True)
        embed.add_field(name="Members", value=f"{guild.member_count:,}", inline=True)
        embed.add_field(name="Humans", value=f"{humans:,}", inline=True)
        embed.add_field(name="Bots", value=f"{bots:,}", inline=True)
        embed.add_field(name="Channels", value=f"💬 {text_channels} text • 🔊 {voice_channels} voice", inline=True)
        embed.add_field(name="Roles", value=str(len(guild.roles)), inline=True)
        embed.add_field(name="Boosts", value=f"Level {guild.premium_tier} • {guild.premium_subscription_count or 0}", inline=True)
        embed.add_field(name="Created", value=f"<t:{int(guild.created_at.timestamp())}:F>", inline=False)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="avatar", description="Show a member's avatar")
    @app_commands.describe(member="Member whose avatar you want")
    async def avatar(interaction: discord.Interaction, member: discord.Member | None = None):
        member = member or interaction.user
        embed = discord.Embed(title=f"🖼️ {member.display_name}'s Avatar")
        embed.set_image(url=member.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="servericon", description="Show this server's icon")
    async def servericon(interaction: discord.Interaction):
        if interaction.guild is None:
            return await interaction.response.send_message("❌ Server only.", ephemeral=True)
        if not interaction.guild.icon:
            return await interaction.response.send_message("❌ This server has no icon.", ephemeral=True)
        embed = discord.Embed(title=f"🖼️ {interaction.guild.name} Icon")
        embed.set_image(url=interaction.guild.icon.url)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="roleinfo", description="Show information about a role")
    @app_commands.describe(role="Role to inspect")
    async def roleinfo(interaction: discord.Interaction, role: discord.Role):
        embed = discord.Embed(title=f"🎭 Role Information • {role.name}", color=role.color)
        embed.add_field(name="Role ID", value=str(role.id), inline=True)
        embed.add_field(name="Members", value=str(len(role.members)), inline=True)
        embed.add_field(name="Position", value=str(role.position), inline=True)
        embed.add_field(name="Mentionable", value="Yes" if role.mentionable else "No", inline=True)
        embed.add_field(name="Hoisted", value="Yes" if role.hoist else "No", inline=True)
        embed.add_field(name="Created", value=f"<t:{int(role.created_at.timestamp())}:F>", inline=False)
        await interaction.response.send_message(embed=embed)
