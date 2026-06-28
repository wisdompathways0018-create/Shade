import os
import discord
from discord.ext import commands
import random

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

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
    "Hi! 😄",
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

"who asked": [
    "Apparently you did. 😂",
    "Interesting question.",
    "Someone had to."
],

"im cooked": [
    "Absolutely cooked. 🍳",
    "Beyond saving.",
    "RIP."
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
    if message.author.bot:
        return

    text = message.content.lower()

if "what's my name" in text or "what is my name" in text:
    await message.channel.send(f"Your name is **{message.author.display_name}** 😎")
    return

if "who am i" in text:
    await message.channel.send(f"You're **{message.author.display_name}** 👑")
    return

for trigger, reply_list in responses.items():
    if trigger in text:
        await message.channel.send(random.choice(reply_list))
        break


    await bot.process_commands(message)

bot.run(TOKEN)