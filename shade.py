import os
import random

import discord
from discord.ext import commands
from discord import app_commands

from config import get_server, save_server

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")
    print(f"🤖 Logged in as {bot.user}")


@bot.tree.command(name="king", description="Choose today's King")
async def king(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
        return
    members = [m for m in interaction.guild.members if not m.bot]
    if not members:
        await interaction.response.send_message("👑 No members found.")
        return
    chosen = random.choice(members)
    messages = [f"👑 Today's King is {chosen.mention}! Long live the King!", f"🏆 The crown chooses {chosen.mention} today!", f"⚔️ All hail {chosen.mention}, ruler of the server!", f"🎉 {chosen.mention} has claimed the throne!"]
    await interaction.response.send_message(random.choice(messages))


@bot.tree.command(name="rate", description="Rate a member")
@app_commands.describe(member="Choose a member")
async def rate(interaction: discord.Interaction, member: discord.Member):
    score = random.randint(0, 100)
    comments = ["💀 Absolutely cooked.", "😂 Could be better.", "😎 Pretty decent!", "🔥 Looking strong!", "👑 Legendary!"]
    await interaction.response.send_message(f"{member.mention} gets **{score}/100**!\n{random.choice(comments)}")


@bot.tree.command(name="roast", description="Roast a member")
@app_commands.describe(member="Choose a member")
async def roast(interaction: discord.Interaction, member: discord.Member):
    roasts = [f"💀 {member.mention} donates more troops than they kill.", f"🏰 {member.mention} thinks gathering counts as PvP.", f"😂 {member.mention} loses castles faster than gathering nodes.", f"🔥 {member.mention} marches so late the battle is already over.", f"⚔️ {member.mention}'s immortals are on permanent vacation.", f"📉 {member.mention}'s STP is just for decoration.", f"❄️ {member.mention} thinks Frost is a farming event.", f"🎯 {member.mention} couldn't rally a barn door.", f"💀 {member.mention} is the reason R5 keeps sending reminder mails.", f"👑 If excuses earned merit, {member.mention} would rank first."]
    await interaction.response.send_message(random.choice(roasts))


@bot.tree.command(name="alliance", description="Set your alliance name")
@app_commands.describe(name="Alliance name")
async def alliance(interaction: discord.Interaction, name: str):
    if interaction.guild is None:
        await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
        return
    config = get_server(interaction.guild.id)
    config["alliance_name"] = name
    save_server()
    await interaction.response.send_message(f"✅ Alliance set to **{name}**")


@bot.tree.command(name="timezone", description="Set your alliance timezone")
@app_commands.describe(timezone="Example: UTC+5:30")
async def timezone(interaction: discord.Interaction, timezone: str):
    if interaction.guild is None:
        await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
        return
    config = get_server(interaction.guild.id)
    config["timezone"] = timezone
    save_server()
    await interaction.response.send_message(f"🌍 Timezone updated to **{timezone}**")


@bot.tree.command(name="pingrole", description="Set the role to ping for reminders")
@app_commands.describe(role="Select a role")
async def pingrole(interaction: discord.Interaction, role: discord.Role):
    if interaction.guild is None:
        await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
        return
    config = get_server(interaction.guild.id)
    config["ping_role"] = role.id
    save_server()
    await interaction.response.send_message(f"✅ Ping role set to {role.mention}")


def channel_command(name, description, config_key, message):
    @bot.tree.command(name=name, description=description)
    @app_commands.describe(channel="Select a text channel")
    async def command(interaction: discord.Interaction, channel: discord.TextChannel):
        if interaction.guild is None:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return
        config = get_server(interaction.guild.id)
        config[config_key] = channel.id
        save_server()
        await interaction.response.send_message(message.format(channel=channel))
    return command


channel_command("frostchannel", "Set the Frost announcement channel", "frost_channel", "✅ Frost announcements will be sent to {channel.mention}")
channel_command("kechannel", "Set the Kill Event announcement channel", "ke_channel", "✅ Kill Event announcements will be sent to {channel.mention}")
channel_command("ibchannel", "Set the IB announcement channel", "ib_channel", "✅ IB announcements will be sent to {channel.mention}")
channel_command("aschannel", "Set the Alliance Supremacy announcement channel", "as_channel", "✅ Alliance Supremacy announcements will be sent to {channel.mention}")
channel_command("corchannel", "Set the Contention of Relics announcement channel", "cor_channel", "✅ Contention of Relics announcements will be sent to {channel.mention}")
channel_command("malenachannel", "Set the Malena announcement channel", "malena_channel", "✅ Malena announcements will be sent to {channel.mention}")


@bot.tree.command(name="setup", description="View your Shade configuration")
async def setup(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
        return
    config = get_server(interaction.guild.id)
    embed = discord.Embed(title="🌑 Shade Configuration", color=discord.Color.dark_gray())
    embed.add_field(name="Alliance", value=config.get("alliance_name") or "Not Set", inline=False)
    embed.add_field(name="Timezone", value=config.get("timezone") or "UTC", inline=False)
    role = interaction.guild.get_role(config["ping_role"]) if config.get("ping_role") else None
    embed.add_field(name="Ping Role", value=role.mention if role else "Not Set", inline=False)
    for title, key in [("❄️ Frost", "frost_channel"), ("🏰 Iron Bastion", "ib_channel"), ("⚔️ Kill Event", "ke_channel"), ("🏆 Alliance Supremacy", "as_channel"), ("🗿 Contention of Relics", "cor_channel"), ("👑 Malena", "malena_channel")]:
        channel = interaction.guild.get_channel(config[key]) if config.get(key) else None
        embed.add_field(name=title, value=channel.mention if channel else "Not Set", inline=False)
    warnings = config.get("moderation_warnings", {})
    embed.add_field(name="🛡️ Moderation Warnings", value=str(sum(warnings.values())), inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    try:
        if interaction.response.is_done():
            await interaction.followup.send(f"❌ Error: {error}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Error: {error}", ephemeral=True)
    except Exception as e:
        print(e)


import events
import reminders
import roles
import ib
import ke
import supremacy
import cor
import malena
import moderation
import universal
import community
import info_commands

events.setup(bot)
reminders.setup(bot)
roles.setup(bot)
ib.setup(bot)
ke.setup(bot)
supremacy.setup(bot)
cor.setup(bot)
malena.setup(bot)
moderation.setup(bot)
universal.setup(bot)
community.setup(bot)
info_commands.setup(bot)


if __name__ == "__main__":
    bot.run(TOKEN)
