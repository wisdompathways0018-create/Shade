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
intents.invites = True

bot = commands.Bot(command_prefix="!", intents=intents)

_universal_modules_loaded = False


@bot.event
async def on_ready():
    global _universal_modules_loaded

    # universal.py and community.py start background tasks. They must be
    # initialized after Discord has created the running event loop.
    if not _universal_modules_loaded:
        universal.setup(bot)
        community.setup(bot)
        bot.add_view(TruthDareView())
        _universal_modules_loaded = True

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


# Each server/member gets a shuffled roast deck so Shade does not repeat a roast
# until it has used every roast in the deck.
_roast_bags: dict[tuple[int, int], list[int]] = {}


@bot.tree.command(name="roast", description="Roast a member")
@app_commands.describe(member="Choose a member")
async def roast(interaction: discord.Interaction, member: discord.Member):
    roasts = [
        f"💀 {member.mention} donates more troops than they kill.",
        f"🏰 {member.mention} thinks gathering counts as PvP.",
        f"😂 {member.mention} loses castles faster than gathering nodes.",
        f"🔥 {member.mention} marches so late the battle is already over.",
        f"⚔️ {member.mention}'s immortals are on permanent vacation.",
        f"📉 {member.mention}'s STP is just for decoration.",
        f"❄️ {member.mention} thinks Frost is a farming event.",
        f"🎯 {member.mention} couldn't rally a barn door.",
        f"💀 {member.mention} is the reason R5 keeps sending reminder mails.",
        f"👑 If excuses earned merit, {member.mention} would rank first.",
    ]

    key = (interaction.guild.id if interaction.guild else 0, member.id)
    bag = _roast_bags.setdefault(key, [])
    if not bag:
        bag.extend(range(len(roasts)))
        random.shuffle(bag)

    roast_text = roasts[bag.pop()]
    await interaction.response.send_message(roast_text)


TRUTH_PROMPTS = [
    "What is the most embarrassing thing you've done in front of the alliance?",
    "Which game do you secretly spend way too much time playing?",
    "What is your biggest gaming rage moment?",
    "Who in this server would you trust to lead you into battle?",
    "What is one skill you wish you were better at?",
    "What is the funniest excuse you've ever used?",
    "What is the weirdest food combination you actually enjoy?",
    "What is a harmless secret you've never told the server?",
    "What is the last thing that made you laugh really hard?",
    "If you could instantly master one skill, what would it be?",
    "What is your most questionable gaming strategy?",
    "What is one thing you would change about your playstyle?",
]

DARE_PROMPTS = [
    "Send the last meme saved on your phone.",
    "Change your server nickname to something silly for 10 minutes.",
    "Send a message using only emojis.",
    "Compliment the person who last sent a message in this channel.",
    "Type your next message with your eyes closed.",
    "Send a dramatic battle speech in this channel.",
    "Use three completely unrelated emojis in your next message.",
    "Say 'I am the greatest strategist alive' with complete confidence.",
    "Post your best one-line joke in this channel.",
    "React to the next message with the most unexpected emoji you can find.",
    "Describe your current mood using only a movie title.",
    "Challenge someone to a friendly /roast battle.",
]


def _truth_dare_embed(interaction: discord.Interaction, prompt_type: str, prompt: str) -> discord.Embed:
    if prompt_type == "TRUTH":
        color = discord.Color.green()
        emoji = "🟢"
    elif prompt_type == "DARE":
        color = discord.Color.red()
        emoji = "🔴"
    else:
        color = discord.Color.blurple()
        emoji = "🎲"

    embed = discord.Embed(
        title=f"{emoji} {prompt}",
        color=color,
    )
    embed.set_footer(text=f"Type: {prompt_type} • Requested by {interaction.user.display_name}")
    embed.set_author(
        name=f"Requested by {interaction.user.display_name}",
        icon_url=interaction.user.display_avatar.url,
    )
    return embed


class TruthDareView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def _send_prompt(self, interaction: discord.Interaction, prompt_type: str):
        if prompt_type == "TRUTH":
            prompt = random.choice(TRUTH_PROMPTS)
        elif prompt_type == "DARE":
            prompt = random.choice(DARE_PROMPTS)
        else:
            prompt_type = random.choice(["TRUTH", "DARE"])
            prompt = random.choice(TRUTH_PROMPTS if prompt_type == "TRUTH" else DARE_PROMPTS)

        await interaction.response.edit_message(
            embed=_truth_dare_embed(interaction, prompt_type, prompt),
            view=self,
        )

    @discord.ui.button(label="Truth", emoji="🟢", style=discord.ButtonStyle.success, custom_id="shade:truthdare:truth")
    async def truth_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._send_prompt(interaction, "TRUTH")

    @discord.ui.button(label="Dare", emoji="🔴", style=discord.ButtonStyle.danger, custom_id="shade:truthdare:dare")
    async def dare_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._send_prompt(interaction, "DARE")

    @discord.ui.button(label="Random", emoji="🎲", style=discord.ButtonStyle.primary, custom_id="shade:truthdare:random")
    async def random_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._send_prompt(interaction, "RANDOM")


@bot.tree.command(name="truthdare", description="Start a Truth or Dare game")
async def truthdare(interaction: discord.Interaction):
    prompt_type = random.choice(["TRUTH", "DARE"])
    prompt = random.choice(TRUTH_PROMPTS if prompt_type == "TRUTH" else DARE_PROMPTS)
    await interaction.response.send_message(
        embed=_truth_dare_embed(interaction, prompt_type, prompt),
        view=TruthDareView(),
    )


@bot.tree.command(name="truth", description="Get a random Truth question")
async def truth(interaction: discord.Interaction):
    await interaction.response.send_message(f"🟢 **Truth:** {random.choice(TRUTH_PROMPTS)}")


@bot.tree.command(name="dare", description="Get a random Dare challenge")
async def dare(interaction: discord.Interaction):
    await interaction.response.send_message(f"🔴 **Dare:** {random.choice(DARE_PROMPTS)}")


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

events.setup(bot)
reminders.setup(bot)
roles.setup(bot)
ib.setup(bot)
ke.setup(bot)
supremacy.setup(bot)
cor.setup(bot)
malena.setup(bot)
moderation.setup(bot)


if __name__ == "__main__":
    bot.run(TOKEN)