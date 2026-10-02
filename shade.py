import os
import random

import discord
from discord.ext import commands
from discord import app_commands

from config import get_server, save_server
from owner import OWNER_USER_ID, is_owner

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
        personal.setup(bot)
        bot.add_view(TruthDareView())
        _universal_modules_loaded = True

    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")
    print(f"🤖 Logged in as {bot.user}")


@bot.tree.command(name="shade", description="Show what Shade is")
async def shade(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🌑 Shade is a personal bot built around <@{OWNER_USER_ID}>."
    )

@bot.tree.command(name="owner", description="Show Shade's owner")
async def owner(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🖤 Shade belongs to <@{OWNER_USER_ID}>."
    )

@bot.tree.command(name="shadeabout", description="Show Shade's identity")
async def shadeabout(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🌑 Shade",
        description="A personal Discord bot built around its owner.",
        color=discord.Color.dark_gray(),
    )
    embed.add_field(name="Owner", value=f"<@{OWNER_USER_ID}>", inline=False)
    embed.add_field(
        name="Core",
        value="👑 King • 🔥 Roast • 🎲 Truth • 😈 Dare • 🎲 Truth or Dare",
        inline=False,
    )
    await interaction.response.send_message(embed=embed)

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
_last_roast: dict[tuple[int, int], int] = {}
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
        f"💀 {member.mention} has a PhD in doing absolutely nothing during rallies.",
        f"😂 {member.mention} joins the war after the victory screen appears.",
        f"📉 {member.mention}'s battle report looks like a receipt for donations.",
        f"🔥 {member.mention} brings main-character confidence and NPC damage.",
        f"⚔️ {member.mention} attacks like their march is powered by dial-up.",
        f"🏰 {member.mention} sees an empty castle and somehow still loses.",
        f"💀 {member.mention} has more excuses than troops.",
        f"😂 {member.mention} treats alliance mails like optional terms and conditions.",
        f"📉 {member.mention}'s kill count is taking a personal day.",
        f"🔥 {member.mention} has mastered the art of arriving exactly when it's safe.",
        f"🎯 {member.mention} could miss a target standing still.",
        f"⚔️ {member.mention} rallies so slowly even the timer gets bored.",
        f"👑 {member.mention} wants the crown but keeps donating the throne.",
        f"💀 {member.mention} is undefeated at finding reasons not to fight.",
        f"😂 {member.mention} calls it strategy; everyone else calls it hiding.",
        f"📉 {member.mention}'s STP has been on life support since day one.",
        f"🔥 {member.mention} has legendary confidence and tutorial-level execution.",
        f"🏰 {member.mention} guards castles like they're allergic to attacking.",
        f"⚔️ {member.mention} presses march and immediately regrets it.",
        f"💀 {member.mention} is proof that power and skill are separate stats.",
        f"😂 {member.mention} studies battle reports like they're horror stories.",
        f"📉 {member.mention}'s troops deserve a more active commander.",
        f"🔥 {member.mention} has never met a farming node they wouldn't choose over PvP.",
        f"🎯 {member.mention} aims with vibes and attacks with hope.",
        f"⚔️ {member.mention}'s march speed is faster than their decision-making.",
        f"👑 {member.mention} has the confidence of R5 and the activity of a ghost.",
        f"💀 {member.mention} is always ready to fight... tomorrow.",
        f"😂 {member.mention} turns every battle into a donation campaign.",
        f"📉 {member.mention}'s war strategy is basically 'maybe next time'.",
        f"🔥 {member.mention} has a sixth sense for avoiding every important fight.",
        f"🏰 {member.mention} protects their troops so well nobody ever sees them.",
        f"⚔️ {member.mention} could turn a winning rally into a group project.",
        f"💀 {member.mention} has enough unused stamina to power the whole kingdom.",
        f"😂 {member.mention} logs in just long enough to collect rewards and disappear.",
        f"📉 {member.mention}'s combat report needs a sympathy button.",
        f"🔥 {member.mention} is the human version of a missed rally timer.",
        f"🎯 {member.mention} could lose a 1v1 against a tutorial pop-up.",
        f"⚔️ {member.mention} has the battle instincts of a loading screen.",
        f"👑 {member.mention} wants MVP but plays like they're AFK.",
        f"💀 {member.mention} makes retreat look like an advanced strategy.",
        f"😂 {member.mention} has more saved troops than completed attacks.",
        f"📉 {member.mention}'s PvP career is still waiting for its first chapter.",
        f"🔥 {member.mention} doesn't chase glory; glory actively avoids them.",
        f"🏰 {member.mention} treats every enemy castle like a sightseeing destination.",
        f"⚔️ {member.mention} attacks with the confidence of someone who forgot to check the stats.",
        f"💀 {member.mention} is the reason battle timers come with warning labels.",
        f"😂 {member.mention} has perfected the art of being present but unavailable.",
        f"📉 {member.mention}'s biggest enemy is the attack button.",
        f"🔥 {member.mention} has never let facts interfere with a good battle plan.",

    ]

    key = (interaction.guild.id if interaction.guild else 0, member.id)
    bag = _roast_bags.setdefault(key, [])
    if not bag:
        bag.extend(range(len(roasts)))
        random.shuffle(bag)

        # Prevent the final roast of one cycle from being the first roast
        # of the next cycle.
        previous = _last_roast.get(key)
        if previous is not None and len(bag) > 1 and bag[-1] == previous:
            bag[-1], bag[-2] = bag[-2], bag[-1]

    selected = bag.pop()
    _last_roast[key] = selected
    roast_text = roasts[selected]
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
    "If you had to kiss one person here, who would you choose?",    "What is a habit you have that you would never want your partner to know about?",
    "What is the pettiest reason you have ever stopped talking to someone?",
    "What is something you pretend to understand but actually do not?",
    "Who was the last person who made you genuinely nervous?",
    "What is the biggest mistake you made in a relationship?",
    "What is something you have done just because you wanted someone to like you?",
    "Have you ever deleted a message because you were embarrassed by how eager it sounded?",
    "What is the longest you have gone without replying to someone on purpose?",
    "What is one opinion you have that most people around you would disagree with?",
    "What is the most childish argument you have ever had with someone?",
    "Have you ever lied about where you were going?",
    "What is one thing you judge people for even though you know you should not?",
    "What is the most awkward thing that has happened while you were trying to impress someone?",
    "Have you ever had a crush on someone who had no idea?",
    "What is one compliment you still remember years later?",
    "What is the most embarrassing thing in your search history that you can safely admit?",
    "What is something you would change about your personality if you could?",
    "Have you ever acted like you did not care when you actually cared a lot?",
    "What is the worst excuse you have used to avoid someone?",
    "What is one secret you kept from your closest friend for a long time?",
    "What is the most impulsive purchase you have ever made?",
    "Have you ever reread an old conversation because you missed someone?",
    "What is something you wish you had said to someone but never did?",
    "What is the most awkward compliment you have ever received?",
    "Have you ever been jealous of a friend's relationship?",
    "What is one thing you would never post publicly but would admit here?",
    "What is the biggest misconception people have about your dating life?",
    "Have you ever pretended to be busy because you did not want to talk to someone?",
    "What is the most ridiculous thing you have done while trying to look cool?",
    "What is one boundary you learned the hard way to set in relationships?",
    "Have you ever caught yourself developing feelings for someone unexpectedly?",
    "What is the most awkward message you have ever received from a crush?",
    "What is one thing you would do differently in your last relationship?",
    "Have you ever stayed in contact with someone mainly because you hoped something romantic would happen?",
    "What is the most embarrassing nickname someone has given you?",
    "What is one thing you secretly enjoy that your friends would be surprised by?",
    "Have you ever lied and said you were fine when you absolutely were not?",
    "What is the most memorable first date you have ever had?",
    "What is one thing you would want your future partner to understand about you?",
    "What is the biggest risk you have taken for someone you cared about?",
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



_generated_truths: dict[int, set[str]] = {}

def _generate_truth_question(guild_id: int) -> str:
    """Generate a fresh local Truth question without an external API."""
    topics = [
        "your relationships", "your friendships", "your dating life", "your work life",
        "your family", "your habits", "your personality", "your ambitions",
        "your biggest mistakes", "your social life", "your past", "your future",
    ]
    subjects = [
        "a person you used to know", "your closest friend", "someone you had a crush on",
        "someone you recently met", "your partner or ex", "yourself five years ago",
        "someone you secretly admire", "a person you wish you understood better",
    ]
    actions = [
        "ignored", "missed", "misjudged", "lied to", "apologized to", "wanted to impress",
        "wanted to avoid", "felt jealous of", "developed feelings for", "trusted too quickly",
    ]
    endings = [
        "and why?", "and what happened next?", "and would you do it differently now?",
        "and what did you learn from it?", "and would you admit it to them?",
        "and how did it change you?", "and what would you do if it happened again?",
    ]
    templates = [
        "What is one thing about {topic} that you rarely admit?",
        "What is the biggest lesson {topic} has taught you?",
        "What is something you wish people understood about you when it comes to {topic}?",
        "What is the most awkward moment you remember involving {subject}?",
        "When was the last time you {action} {subject}, {ending}",
        "What is one decision involving {topic} that you would make differently today?",
        "What is something you have hidden about {topic} because you were embarrassed?",
        "What is one thing you are proud of about {topic}?",
        "What is one thing about {topic} that you would change if you had the chance?",
        "What is the most unexpected thing {subject} has made you realize about yourself?",
    ]

    seen = _generated_truths.setdefault(guild_id, set())
    for _ in range(100):
        template = random.choice(templates)
        question = template.format(
            topic=random.choice(topics),
            subject=random.choice(subjects),
            action=random.choice(actions),
            ending=random.choice(endings),
        )
        if question not in seen:
            seen.add(question)
            return question

    # Extremely unlikely fallback after a very large generated cycle.
    return _next_prompt(TRUTH_PROMPTS, _truth_bags, _last_truth, guild_id)


def _next_truth_prompt(guild_id: int) -> str:
    return _generate_truth_question(guild_id)


def _truth_dare_embed(interaction: discord.Interaction, prompt_type: str, prompt: str) -> discord.Embed:
    embed = discord.Embed(
        title="🎲 Truth or Dare",
        description=prompt,
        color=discord.Color.blurple(),
    )
    embed.add_field(name="Requested by", value=interaction.user.mention, inline=True)
    embed.add_field(name="Type", value=prompt_type, inline=True)
    return embed


class TruthDareView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def _send_prompt(self, interaction: discord.Interaction, prompt_type: str):
        guild_id = interaction.guild.id if interaction.guild else 0

        if prompt_type == "TRUTH":
            prompt = _next_truth_prompt(guild_id)
        elif prompt_type == "DARE":
            prompt = _next_prompt(DARE_PROMPTS, _dare_bags, _last_dare, guild_id)
        else:
            prompt_type = random.choice(["TRUTH", "DARE"])
            prompt = _next_truth_prompt(guild_id) if prompt_type == "TRUTH" else _next_prompt(DARE_PROMPTS, _dare_bags, _last_dare, guild_id)

        await interaction.response.defer()
        if interaction.channel is not None:
            await interaction.channel.send(
                embed=_truth_dare_embed(interaction, prompt_type, prompt),
                view=TruthDareView(),
            )

    @discord.ui.button(
        label="Truth",
        emoji="🟢",
        style=discord.ButtonStyle.success,
        custom_id="shade:truthdare:truth",
    )
    async def truth_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._send_prompt(interaction, "TRUTH")

    @discord.ui.button(
        label="Dare",
        emoji="🔴",
        style=discord.ButtonStyle.danger,
        custom_id="shade:truthdare:dare",
    )
    async def dare_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._send_prompt(interaction, "DARE")

    @discord.ui.button(
        label="Random",
        emoji="🎲",
        style=discord.ButtonStyle.primary,
        custom_id="shade:truthdare:random",
    )
    async def random_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._send_prompt(interaction, "RANDOM")


@bot.tree.command(name="truthdare", description="Start a Truth or Dare game")
async def truthdare(interaction: discord.Interaction):
    prompt_type = random.choice(["TRUTH", "DARE"])
    prompt = _next_truth_prompt(interaction.guild.id if interaction.guild else 0) if prompt_type == "TRUTH" else _next_prompt(DARE_PROMPTS, _dare_bags, _last_dare, interaction.guild.id if interaction.guild else 0)
    await interaction.response.send_message(
        embed=_truth_dare_embed(interaction, prompt_type, prompt),
        view=TruthDareView(),
    )


@bot.tree.command(name="truth", description="Get a random Truth question")
async def truth(interaction: discord.Interaction):
    await interaction.response.send_message(f"🟢 **Truth:** {_next_truth_prompt(interaction.guild.id if interaction.guild else 0)}")


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


@bot.tree.command(name="timezone", description="Set your timezone")
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
    embed = discord.Embed(title="🌑 Shade • Personal Configuration", color=discord.Color.dark_gray())
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
import personal

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