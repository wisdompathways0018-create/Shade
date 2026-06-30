import os
import random
import time

import discord
from discord.ext import commands
from discord import app_commands

from config import get_server, save_server

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

last_reply = 0

responses = {
    "hi": [
        "Hey! 👋",
        "Hello there!",
        "Welcome!"
    ],

    "hello": [
        "Hi! 😊",
        "Greetings!"
    ],

    "gg": [
        "GG! 🔥",
        "Well played!"
    ],

    "thanks": [
        "You're welcome! ❤️",
        "Anytime!"
    ],

    "lol": [
        "🤣",
        "😂"
    ],

    "shadow": [
        "🌑 Shadow Sovereign has arrived.",
        "Darkness answers your call."
    ],

    "oops": [
        "Mission failed successfully 😂",
        "Peak performance."
    ]
}


@bot.event
async def on_ready():

    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

    print(f"🤖 Logged in as {bot.user}")


@bot.event
async def on_message(message):

    global last_reply

    if message.author.bot:
        return

    text = message.content.lower()

    for trigger, reply_list in responses.items():

        if trigger in text:

            if time.time() - last_reply >= 30:

                if random.randint(1, 100) <= 30:

                    await message.channel.send(
                        random.choice(reply_list)
                    )

                    last_reply = time.time()

            break

    await bot.process_commands(message)

# ==========================================
# Fun Slash Commands
# ==========================================

@bot.tree.command(
    name="king",
    description="Choose today's King"
)
async def king(interaction: discord.Interaction):

    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ This command can only be used in a server.",
            ephemeral=True
        )
        return

    members = [
        m for m in interaction.guild.members
        if not m.bot
    ]

    if not members:
        await interaction.response.send_message(
            "👑 No members found."
        )
        return

    chosen = random.choice(members)

    messages = [
        f"👑 Today's King is {chosen.mention}! Long live the King!",
        f"🏆 The crown chooses {chosen.mention} today!",
        f"⚔️ All hail {chosen.mention}, ruler of the server!",
        f"🎉 {chosen.mention} has claimed the throne!"
    ]

    await interaction.response.send_message(
        random.choice(messages)
    )


@bot.tree.command(
    name="rate",
    description="Rate a member"
)
@app_commands.describe(
    member="Choose a member"
)
async def rate(
    interaction: discord.Interaction,
    member: discord.Member
):

    score = random.randint(0, 100)

    comments = [
        "💀 Absolutely cooked.",
        "😂 Could be better.",
        "😎 Pretty decent!",
        "🔥 Looking strong!",
        "👑 Legendary!"
    ]

    await interaction.response.send_message(
        f"{member.mention} gets **{score}/100**!\n{random.choice(comments)}"
    )


@bot.tree.command(
    name="roast",
    description="Roast a member"
)
@app_commands.describe(
    member="Choose a member"
)
async def roast(
    interaction: discord.Interaction,
    member: discord.Member
):

    roasts = [
        f"💀 {member.mention} has a better chance of tripping over Wi-Fi than winning.",
        f"😂 {member.mention} plays so badly even tutorials feel insulted.",
        f"🤡 {member.mention} is living proof that confidence isn't the same as skill.",
        f"📉 {member.mention}'s gameplay should be classified as a natural disaster.",
        f"🎮 {member.mention} is the reason the enemy team smiles.",
        f"🗑️ {member.mention} couldn't carry a backpack, let alone the team.",
        f"☠️ {member.mention} has mastered the art of spectacular failure.",
        f"🔥 {member.mention} is the MVP... for the opposing team."
    ]

    await interaction.response.send_message(
        random.choice(roasts)
    )

# ==========================================
# Alliance Setup Commands
# ==========================================

@bot.tree.command(
    name="alliance",
    description="Set your alliance name"
)
@app_commands.describe(
    name="Alliance name"
)
async def alliance(
    interaction: discord.Interaction,
    name: str
):

    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ This command can only be used in a server.",
            ephemeral=True
        )
        return

    config = get_server(interaction.guild.id)

    config["alliance_name"] = name
    save_server()

    await interaction.response.send_message(
        f"✅ Alliance set to **{name}**"
    )


@bot.tree.command(
    name="timezone",
    description="Set your alliance timezone"
)
@app_commands.describe(
    timezone="Example: UTC+5:30"
)
async def timezone(
    interaction: discord.Interaction,
    timezone: str
):

    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ This command can only be used in a server.",
            ephemeral=True
        )
        return

    config = get_server(interaction.guild.id)

    config["timezone"] = timezone
    save_server()

    await interaction.response.send_message(
        f"🌍 Timezone updated to **{timezone}**"
    )


@bot.tree.command(
    name="pingrole",
    description="Set the role to ping for reminders"
)
@app_commands.describe(
    role="Select a role"
)
async def pingrole(
    interaction: discord.Interaction,
    role: discord.Role
):

    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ This command can only be used in a server.",
            ephemeral=True
        )
        return

    config = get_server(interaction.guild.id)

    config["ping_role"] = role.id
    save_server()

    await interaction.response.send_message(
        f"✅ Ping role set to {role.mention}"
    )


@bot.tree.command(
    name="eventchannel",
    description="Set the reminder channel"
)
@app_commands.describe(
    channel="Select a text channel"
)
async def eventchannel(
    interaction: discord.Interaction,
    channel: discord.TextChannel
):

    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ This command can only be used in a server.",
            ephemeral=True
        )
        return

    config = get_server(interaction.guild.id)

    config["reminder_channel"] = channel.id
    save_server()

    await interaction.response.send_message(
        f"✅ Reminder channel set to {channel.mention}"
    )


@bot.tree.command(
    name="setup",
    description="View your Shade configuration"
)
async def setup(interaction: discord.Interaction):

    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ This command can only be used in a server.",
            ephemeral=True
        )
        return

    config = get_server(interaction.guild.id)

    embed = discord.Embed(
        title="🌑 Shade Configuration",
        color=discord.Color.dark_gray()
    )

    embed.add_field(
        name="Alliance",
        value=config.get("alliance_name") or "Not Set",
        inline=False
    )

    embed.add_field(
        name="Timezone",
        value=config.get("timezone") or "UTC",
        inline=False
    )

    if config.get("ping_role"):
        role = interaction.guild.get_role(config["ping_role"])
        ping = role.mention if role else "Unknown Role"
    else:
        ping = "Not Set"

    embed.add_field(
        name="Ping Role",
        value=ping,
        inline=False
    )

    if config.get("reminder_channel"):
        channel = interaction.guild.get_channel(
            config["reminder_channel"]
        )
        reminder = channel.mention if channel else "Unknown Channel"
    else:
        reminder = "Not Set"

    embed.add_field(
        name="Reminder Channel",
        value=reminder,
        inline=False
    )

    await interaction.response.send_message(
        embed=embed
    )

# ==========================================
# Global Error Handler
# ==========================================

@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError
):

    try:

        if interaction.response.is_done():

            await interaction.followup.send(
                f"❌ Error: {error}",
                ephemeral=True
            )

        else:

            await interaction.response.send_message(
                f"❌ Error: {error}",
                ephemeral=True
            )

    except Exception as e:
        print(e)

import events

events.setup(bot)

# import reminders
# reminders.setup(bot)


# ==========================================
# Start Shade
# ==========================================

if __name__ == "__main__":
    bot.run(TOKEN)