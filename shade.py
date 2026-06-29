import os
import random
import time
import discord
from discord.ext import commands
from config import get_server

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

last_reply = 0

responses = {
    "oops": [
        "😂 Nice one.",
        "Mission failed successfully.",
        "Peak performance."
    ],
    "lost": [
        "💀 Skill issue detected.",
        "GG... for the other side.",
        "That didn't go as planned."
    ],
    "hi": [
        "Hey! 👋",
        "Hello there!",
        "Welcome!"
    ],
    "hello": [
        "Hi! 😊",
        "Greetings!",
        "Hey, how's it going?"
    ],
    "bye": [
        "See you later! 👋",
        "Take care!",
        "Goodbye!"
    ],
    "thanks": [
        "You're welcome! ❤️",
        "Anytime!",
        "Glad to help!"
    ],
    "gg": [
        "GG! 🔥",
        "Well played!",
        "Respect."
    ],
    "ez": [
        "😂 Sure it was.",
        "Confidence level: 100%.",
        "We'll allow it."
    ],
    "win": [
        "Victory! 🏆",
        "Let's gooo! 🔥",
        "Champion vibes!"
    ],
    "lose": [
        "You'll get them next time.",
        "Every loss is a lesson.",
        "Keep fighting!"
    ],
    "lol": [
        "🤣",
        "LMAO 😂",
        "That was funny!"
    ],
    "bot": [
        "Yes? I'm awake. 🤖",
        "At your service!",
        "What's up?"
    ],
    "shadow": [
        "Shadow Sovereign has arrived. 🌑",
        "Darkness answers your call.",
        "All hail the Shadow."
    ],
    "help": [
        "How can I help?",
        "Type something interesting!",
        "I'm listening."
    ],
    "let him cook": [
        "We'll see if it burns. 🔥",
        "Cooking in progress...",
        "Chef mode activated."
    ],
    "nah": [
        "Understandable.",
        "Fair enough.",
        "No means no."
    ],
    "brb": [
        "I'll be here.",
        "Take your time.",
        "Don't get lost."
    ]
}


@bot.event
async def on_ready():
    print(f"{bot.user} is online!")


@bot.event
async def on_message(message):
    global last_reply

    if message.author.bot:
        return

    text = message.content.lower()
    config = get_server(message.guild.id) if message.guild else None

    # What's my name
    if "what's my name" in text or "what is my name" in text:
        await message.channel.send(
            f"Your name is **{message.author.display_name}** 😎"
        )
        return

    # Who am I
    if "who am i" in text:
        await message.channel.send(
            f"You're **{message.author.display_name}** 👑"
        )
        return

    # Auto replies (30 sec cooldown + 30% chance)
    for trigger, reply_list in responses.items():
        if trigger in text:
            if time.time() - last_reply >= 30:
                if random.randint(1, 100) <= 30:
                    await message.channel.send(random.choice(reply_list))
                    last_reply = time.time()
            break

    # Rate command
    if text.startswith("rate ") and message.mentions:
        target = message.mentions[0]

        score = random.randint(0, 100)

        comments = [
            "💀 Absolutely cooked.",
            "😂 Could be better.",
            "😎 Pretty decent!",
            "🔥 Looking strong!",
            "👑 Legendary!"
        ]

        await message.channel.send(
            f"{target.mention} gets **{score}/100**!\n{random.choice(comments)}"
        )
        return

    # Roast command
    if text.startswith("roast ") and message.mentions:
        target = message.mentions[0]

        roasts = [
            f"💀 {target.mention} has a better chance of tripping over Wi-Fi than winning.",
            f"😂 {target.mention} plays so badly even tutorials feel insulted.",
            f"🤡 {target.mention} is living proof that confidence isn't the same as skill.",
            f"📉 {target.mention}'s gameplay should be classified as a natural disaster.",
            f"🎮 {target.mention} is the reason the enemy team smiles.",
            f"🗑️ {target.mention} couldn't carry a backpack, let alone the team.",
            f"☠️ {target.mention} has mastered the art of spectacular failure.",
            f"🚪 {target.mention} joined the game just to lower the average IQ.",
            f"🐢 {target.mention} reacts so slowly that the match already ended.",
            f"🔥 {target.mention} is the MVP... for the opposing team."
        ]

        await message.channel.send(random.choice(roasts))
        return

    # King command
    if text == "king":
        if message.guild is None:
            return

        members = [m for m in message.guild.members if not m.bot]

        if not members:
            await message.channel.send("👑 No members found.")
            return

        king = random.choice(members)

        king_messages = [
            f"👑 Today's King is... {king.mention}! Long live the King!",
            f"🏆 The crown chooses {king.mention} today!",
            f"⚔️ All hail {king.mention}, ruler of the server!",
            f"👑 {king.mention} has claimed the throne today.",
            f"🎉 The kingdom belongs to {king.mention}!"
        ]

        await message.channel.send(random.choice(king_messages))
        return
# Alliance command
if text.startswith("!alliance "):
    if config is None:
        return

    alliance_name = message.content[10:].strip()

    if alliance_name == "":
        await message.channel.send("❌ Please enter an alliance name.")
        return

    config["alliance_name"] = alliance_name

    await message.channel.send(
        f"✅ Alliance name set to **{alliance_name}**!"
    )
    return

    await bot.process_commands(message)


bot.run(TOKEN)