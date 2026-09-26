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
_truth_bags: dict[int, list[int]] = {}
_dare_bags: dict[int, list[int]] = {}
_last_truth: dict[int, int] = {}
_last_dare: dict[int, int] = {}

def _next_prompt(prompts: list[str], bags: dict[int, list[int]], last_used: dict[int, int], guild_id: int) -> str:
    bag = bags.setdefault(guild_id, [])
    if not bag:
        bag.extend(range(len(prompts)))
        random.shuffle(bag)
        previous = last_used.get(guild_id)
        if previous is not None and len(bag) > 1 and bag[-1] == previous:
            bag[-1], bag[-2] = bag[-2], bag[-1]
    selected = bag.pop()
    last_used[guild_id] = selected
    return prompts[selected]



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
    "What is the most scandalous thing you have done while completely intoxicated?",
    "What is the most public place you have ever been intimate with someone?",
    "Who is the most prominent or attractive person to ever slide into your direct messages?",
    "What is an unconventional or unusual trait that you find incredibly attractive?",
    "What is a romantic or intimate fantasy you want to try but have not yet?",
    "What is the most embarrassing text message you have accidentally sent to the wrong person?",
    "Have you ever walked in on your parents or roommates doing something private?",
    "What is the worst or weirdest pickup line you have ever used or received?",
    "Have you ever gone skinny dipping, and if so, where and with whom?",
    "What is the last text message you sent to your romantic partner or crush?",
    "What was your exact first impression of the person to your left?",
    "What is the most expensive thing you have bought while drunk?",
    "What minor thing does your partner or best friend do that secretly drives you crazy?",
    "Who is the last person you looked up on social media that you should not have?",
    "What is the biggest lie you have told to get out of a social commitment?",
    "What is one thing you still do now that is completely childish?",
    "What movie or TV show do you secretly love but feel embarrassed to admit?",
    "What is the absolute worst dating experience you have ever had?",
    "Describe your most embarrassing fashion phase or haircut.",
    "What is a bizarre talent you have that nobody in this room knows about?",
    "What is a realistic fear you have that you rarely talk about?",
    "If you could swap lives with anyone in this room for twenty-four hours, who would it be?",
    "What do people most frequently get wrong or misjudge about you?",
    "Have you ever taken credit for something someone else did at work?",
    "Do you have an ex that got away, and would you get back with them?",
    "What is your biggest insecurity regarding your current lifestyle or career?",
    "What is the most illegal thing you have ever done without getting caught?",
    "Who in this room, if anyone, are you most attracted to?",
    "What is the nicest thing and the meanest thing you have said about someone in this room?",
    "What is a secret ambition you have never told anyone because it sounds too unrealistic?",
    "Who was your most unexpected crush?",
    "What’s the biggest lie you’ve told a partner?",
    "Have you ever flirted with someone you knew you shouldn’t?",
    "What’s your biggest turn-on in someone’s personality?",
    "What’s the most embarrassing thing you’ve done for a crush?",
    "Have you ever had feelings for a friend’s partner?",
    "What’s your biggest relationship red flag?",
    "Have you ever secretly stalked someone’s social media?",
    "What’s the most awkward date you’ve ever been on?",
    "Have you ever kissed someone and immediately regretted it?",
    "What’s something you find attractive that most people don’t?",
    "Have you ever pretended to like someone just to get attention?",
    "What’s the boldest move you’ve ever made on someone?",
    "Have you ever had a crush on someone you absolutely shouldn’t?",
    "What’s one secret you’ve never told anyone in this room?",
    "Who in this room would you most likely go on a date with?",
    "What’s your biggest insecurity when dating?",
    "Have you ever gone back to an ex when you knew it was a bad idea?",
    "What’s the most jealous you’ve ever been?",
    "What’s one thing you would never admit to your partner?",
    "Have you ever had a “friends with benefits” situation?",
    "What’s the most adventurous thing you’ve done on a date?",
    "Have you ever sent a message to the wrong person that you really regretted?",
    "What’s your guilty pleasure when it comes to dating or romance?",
    "If you had to kiss one person here, who would you choose?",
]

DARE_PROMPTS = [
    "Send a genuine compliment to the last person you texted.",
    "Text someone you have not spoken to in a while and ask how they are doing.",
    "Send a voice message to someone saying something unexpectedly nice about them.",
    "Tell the group one harmless embarrassing story from your childhood.",
    "Read your most recent sent message out loud.",
    "Send a thank-you message to someone who has helped you recently.",
    "Text a friend asking them to describe you in three words.",
    "Tell someone in the room one sincere compliment you have never told them before.",
    "Write a two-line poem about your current mood and read it aloud.",
    "Tell the group about the most spontaneous thing you have ever done.",
    "Call someone you trust and tell them one thing you appreciate about them.",
    "Tell the group about a hobby or interest you rarely talk about.",
    "Send a voice note singing one line from a song.",
    "Tell the group one thing on your bucket list.",
    "Send a genuine apology to someone if there is a small unresolved misunderstanding.",
    "Tell the group about the most memorable compliment you have ever received.",
    "Share one goal you want to accomplish this year.",
    "Send a random but kind compliment to someone in your contacts.",
    "Tell the group about a food combination you love that other people find strange.",
    "Text a friend: \"Quick question: what is one thing you think I am good at?\"",
    "Give someone in the group a sincere compliment without making it a joke.",
    "Tell the group the most ridiculous excuse you have ever used to cancel plans.",
    "Make up a ridiculous business idea and pitch it in 30 seconds.",
    "Talk about your dream vacation for one minute without saying the destination.",
    "Share one small thing that always makes your day better.",
    "Tell the group one thing you would change about your daily routine.",
    "Send a supportive message to someone who has been stressed recently.",
    "Do your best impression of how you sound when you are half asleep.",
    "Call a friend and say, \"I have something important to tell you,\" then reveal that you just wanted to say hi.",
    "Do your best impression of someone you know for 30 seconds.",
    "Let the group choose a harmless status for you to use for the next 15 minutes.",
    "Show the group the oldest non-private photo in your camera roll.",
    "Send a message containing only three random emojis to the last person who messaged you.",
    "Compliment yourself out loud with three things you genuinely like about yourself.",
    "Let someone choose a song for you and listen to at least 30 seconds of it.",
    "Text someone you care about: \"Hope your day is going well.\"",
    "Share your funniest autocorrect mistake.",
    "Do a 30-second dramatic reenactment of your last minor inconvenience.",
    "Tell the group your ideal weekend without using the words \"relax,\" \"fun,\" or \"sleep.\"",
    "Send a wholesome meme to someone who could use a laugh.",
]

_truth_bags, _last_truth, interaction.guild.id if interaction.guild else 0)
        elif prompt_type == "DARE":
            prompt = _next_prompt(DARE_PROMPTS, _dare_bags, _last_dare, interaction.guild.id if interaction.guild else 0)
        else:
            prompt_type = random.choice(["TRUTH", "DARE"])
            prompt = _next_prompt(TRUTH_PROMPTS if prompt_type == "TRUTH" else DARE_PROMPTS, _truth_bags if prompt_type == "TRUTH" else _dare_bags, _last_truth if prompt_type == "TRUTH" else _last_dare, interaction.guild.id if interaction.guild else 0)

        await interaction.response.defer()
        if interaction.channel is not None:
            await interaction.channel.send(
                embed=_truth_dare_embed(interaction, prompt_type, prompt),
                view=TruthDareView(),
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
    prompt = _next_prompt(TRUTH_PROMPTS if prompt_type == "TRUTH" else DARE_PROMPTS, _truth_bags if prompt_type == "TRUTH" else _dare_bags, _last_truth if prompt_type == "TRUTH" else _last_dare, interaction.guild.id if interaction.guild else 0)
    await interaction.response.send_message(
        embed=_truth_dare_embed(interaction, prompt_type, prompt),
        view=TruthDareView(),
    )


@bot.tree.command(name="truth", description="Get a random Truth question")
async def truth(interaction: discord.Interaction):
    await interaction.response.send_message(f"🟢 **Truth:** {_next_prompt(TRUTH_PROMPTS, _truth_bags, _last_truth, interaction.guild.id if interaction.guild else 0)}")


@bot.tree.command(name="dare", description="Get a random Dare challenge")
async def dare(interaction: discord.Interaction):
    await interaction.response.send_message(f"🔴 **Dare:** {_next_prompt(DARE_PROMPTS, _dare_bags, _last_dare, interaction.guild.id if interaction.guild else 0)}")


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