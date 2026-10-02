import asyncio
import json
import os
import random
import time
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from owner import OWNER_USER_ID


PERSONAL_FILE = "shade_personal.json"


def _load():
    if not os.path.exists(PERSONAL_FILE):
        return {}
    try:
        with open(PERSONAL_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


data = _load()


def _save():
    temporary = PERSONAL_FILE + ".tmp"
    with open(temporary, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(temporary, PERSONAL_FILE)


def _owner_only(interaction: discord.Interaction) -> bool:
    return interaction.user.id == OWNER_USER_ID


def _owner_profile():
    profile = data.setdefault("profile", {})
    profile.setdefault("bio", "Just me and Shade.")
    profile.setdefault("mood", "Unknown")
    profile.setdefault("quotes", [])
    profile.setdefault("notes", [])
    profile.setdefault("memories", [])
    profile.setdefault("journal", [])
    profile.setdefault("todos", [])
    profile.setdefault("reminders", [])
    return profile


async def _reminder_loop(bot: commands.Bot):
    await bot.wait_until_ready()
    while not bot.is_closed():
        now = time.time()
        changed = False
        profile = _owner_profile()
        for reminder in list(profile.get("reminders", [])):
            if reminder.get("sent") or reminder.get("at", 0) > now:
                continue
            user = bot.get_user(OWNER_USER_ID)
            if user is None:
                try:
                    user = await bot.fetch_user(OWNER_USER_ID)
                except discord.HTTPException:
                    user = None
            if user:
                try:
                    await user.send(f"⏰ **Shade Reminder**\n{reminder.get('text', 'Reminder')}")
                    reminder["sent"] = True
                    changed = True
                except discord.HTTPException:
                    pass
        if changed:
            _save()
        await asyncio.sleep(30)


def setup(bot: commands.Bot):
    _owner_profile()

    @bot.tree.command(name="profile", description="Show Shade's owner's profile")
    async def profile(interaction: discord.Interaction):
        p = _owner_profile()
        embed = discord.Embed(title="🌑 Shade Owner", color=discord.Color.dark_gray())
        embed.add_field(name="Owner", value=f"<@{OWNER_USER_ID}>", inline=False)
        embed.add_field(name="Bio", value=p["bio"][:1024], inline=False)
        embed.add_field(name="Mood", value=p["mood"][:1024], inline=True)
        embed.add_field(name="Quotes", value=str(len(p["quotes"])), inline=True)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="bio", description="Set Shade owner's bio")
    @app_commands.describe(text="Your bio")
    async def bio(interaction: discord.Interaction, text: str):
        if not _owner_only(interaction):
            return await interaction.response.send_message("❌ Owner only.", ephemeral=True)
        _owner_profile()["bio"] = text[:500]
        _save()
        await interaction.response.send_message("✅ Your Shade bio was updated.", ephemeral=True)

    @bot.tree.command(name="mood", description="Set Shade owner's mood")
    @app_commands.describe(text="Your current mood")
    async def mood(interaction: discord.Interaction, text: str):
        if not _owner_only(interaction):
            return await interaction.response.send_message("❌ Owner only.", ephemeral=True)
        _owner_profile()["mood"] = text[:200]
        _save()
        await interaction.response.send_message(f"🌑 Mood set to **{text[:200]}**.", ephemeral=True)

    @bot.tree.command(name="quote", description="Save or show one of your quotes")
    @app_commands.describe(text="Quote to save; leave blank to show a saved quote")
    async def quote(interaction: discord.Interaction, text: str | None = None):
        if not _owner_only(interaction):
            return await interaction.response.send_message("❌ Owner only.", ephemeral=True)
        quotes = _owner_profile()["quotes"]
        if text:
            quotes.append(text[:500])
            _save()
            return await interaction.response.send_message("💬 Quote saved.", ephemeral=True)
        if not quotes:
            return await interaction.response.send_message("💬 No saved quotes yet.")
        await interaction.response.send_message(f"💬 **{random.choice(quotes)}**")

    @bot.tree.command(name="note", description="Save a private Shade note")
    @app_commands.describe(text="Note to save")
    async def note(interaction: discord.Interaction, text: str):
        if not _owner_only(interaction):
            return await interaction.response.send_message("❌ Owner only.", ephemeral=True)
        _owner_profile()["notes"].append({"text": text[:1000], "created": time.time()})
        _save()
        await interaction.response.send_message("📝 Private note saved.", ephemeral=True)

    @bot.tree.command(name="notes", description="View your saved Shade notes")
    async def notes(interaction: discord.Interaction):
        if not _owner_only(interaction):
            return await interaction.response.send_message("❌ Owner only.", ephemeral=True)
        notes_list = _owner_profile()["notes"][-10:]
        if not notes_list:
            return await interaction.response.send_message("📝 No notes saved.", ephemeral=True)
        text = "\n".join(f"• {n['text']}" for n in notes_list)
        await interaction.response.send_message(f"📝 **Your latest notes**\n{text}", ephemeral=True)

    @bot.tree.command(name="memory", description="Save or view Shade memories")
    @app_commands.describe(text="Memory to save; leave blank to view recent memories")
    async def memory(interaction: discord.Interaction, text: str | None = None):
        if not _owner_only(interaction):
            return await interaction.response.send_message("❌ Owner only.", ephemeral=True)
        memories = _owner_profile()["memories"]
        if text:
            memories.append({"text": text[:1000], "created": time.time()})
            _save()
            return await interaction.response.send_message("🧠 Memory saved.", ephemeral=True)
        recent = memories[-10:]
        if not recent:
            return await interaction.response.send_message("🧠 No memories saved.", ephemeral=True)
        await interaction.response.send_message(
            "🧠 **Recent memories**\n" + "\n".join(f"• {m['text']}" for m in recent),
            ephemeral=True,
        )

    @bot.tree.command(name="journal", description="Write or read your private Shade journal")
    @app_commands.describe(text="Journal entry; leave blank to read recent entries")
    async def journal(interaction: discord.Interaction, text: str | None = None):
        if not _owner_only(interaction):
            return await interaction.response.send_message("❌ Owner only.", ephemeral=True)
        entries = _owner_profile()["journal"]
        if text:
            entries.append({
                "text": text[:2000],
                "created": datetime.now(timezone.utc).isoformat(),
            })
            _save()
            return await interaction.response.send_message("📖 Journal entry saved.", ephemeral=True)
        recent = entries[-5:]
        if not recent:
            return await interaction.response.send_message("📖 Your journal is empty.", ephemeral=True)
        await interaction.response.send_message(
            "📖 **Recent journal entries**\n" + "\n".join(f"• {e['text']}" for e in recent),
            ephemeral=True,
        )

    @bot.tree.command(name="todo", description="Add or complete a personal Shade todo")
    @app_commands.describe(text="Todo text; prefix with done: to complete a matching todo")
    async def todo(interaction: discord.Interaction, text: str):
        if not _owner_only(interaction):
            return await interaction.response.send_message("❌ Owner only.", ephemeral=True)
        todos = _owner_profile()["todos"]
        if text.lower().startswith("done:"):
            target = text[5:].strip().lower()
            for item in todos:
                if item["text"].lower() == target and not item["done"]:
                    item["done"] = True
                    _save()
                    return await interaction.response.send_message("✅ Todo completed.", ephemeral=True)
            return await interaction.response.send_message("❌ Todo not found.", ephemeral=True)
        todos.append({"text": text[:500], "done": False})
        _save()
        await interaction.response.send_message("📋 Todo added.", ephemeral=True)

    @bot.tree.command(name="todos", description="Show your personal Shade todos")
    async def todos(interaction: discord.Interaction):
        if not _owner_only(interaction):
            return await interaction.response.send_message("❌ Owner only.", ephemeral=True)
        pending = [x["text"] for x in _owner_profile()["todos"] if not x["done"]]
        if not pending:
            return await interaction.response.send_message("📋 No pending todos.", ephemeral=True)
        await interaction.response.send_message(
            "📋 **Pending todos**\n" + "\n".join(f"• {x}" for x in pending),
            ephemeral=True,
        )

    @bot.tree.command(name="remind", description="Set a private Shade reminder")
    @app_commands.describe(when="UTC time: YYYY-MM-DD HH:MM", text="Reminder text")
    async def remind(interaction: discord.Interaction, when: str, text: str):
        if not _owner_only(interaction):
            return await interaction.response.send_message("❌ Owner only.", ephemeral=True)
        try:
            dt = datetime.strptime(when, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        except ValueError:
            return await interaction.response.send_message(
                "❌ Use UTC format **YYYY-MM-DD HH:MM**.", ephemeral=True
            )
        if dt.timestamp() <= time.time():
            return await interaction.response.send_message("❌ That time is already in the past.", ephemeral=True)
        _owner_profile()["reminders"].append({"at": dt.timestamp(), "text": text[:1000], "sent": False})
        _save()
        await interaction.response.send_message(
            f"⏰ Reminder saved for **{dt.strftime('%Y-%m-%d %H:%M UTC')}**.",
            ephemeral=True,
        )

    @bot.tree.command(name="coinflip", description="Flip a coin")
    async def coinflip(interaction: discord.Interaction):
        await interaction.response.send_message(f"🪙 **{random.choice(['Heads', 'Tails'])}!**")

    @bot.tree.command(name="8ball", description="Ask Shade the magic 8-ball")
    @app_commands.describe(question="Your question")
    async def eightball(interaction: discord.Interaction, question: str):
        answers = [
            "Absolutely.", "Probably.", "Ask again later.", "Maybe.",
            "Not a chance.", "I wouldn't count on it.", "Definitely.",
            "The Shade has spoken."
        ]
        await interaction.response.send_message(f"🎱 **{random.choice(answers)}**")

    @bot.tree.command(name="choose", description="Let Shade choose between options")
    @app_commands.describe(options="Separate choices with |")
    async def choose(interaction: discord.Interaction, options: str):
        choices = [x.strip() for x in options.split("|") if x.strip()]
        if len(choices) < 2:
            return await interaction.response.send_message("❌ Give me at least two choices.")
        await interaction.response.send_message(f"🎯 Shade chooses **{random.choice(choices)}**")

    @bot.tree.command(name="dice", description="Roll a die")
    @app_commands.describe(sides="Number of sides")
    async def dice(interaction: discord.Interaction, sides: app_commands.Range[int, 2, 100] = 6):
        await interaction.response.send_message(f"🎲 You rolled **{random.randint(1, sides)}** / {sides}")

    @bot.tree.command(name="wouldyourather", description="Ask a would-you-rather question")
    async def wouldyourather(interaction: discord.Interaction):
        prompts = [
            "Would you rather know the truth about your future or be able to change one past decision?",
            "Would you rather always be 10 minutes early or always be 20 minutes late?",
            "Would you rather have unlimited money or unlimited free time?",
            "Would you rather read minds or become invisible?",
            "Would you rather never lose your phone or never lose your wallet?",
            "Would you rather travel anywhere instantly or never need to sleep?",
        ]
        await interaction.response.send_message(f"🤔 **{random.choice(prompts)}**")

    @bot.tree.command(name="neverhaveiever", description="Get a Never Have I Ever prompt")
    async def neverhaveiever(interaction: discord.Interaction):
        prompts = [
            "Never have I ever lied about why I was late.",
            "Never have I ever stalked someone's social media.",
            "Never have I ever sent a message to the wrong person.",
            "Never have I ever pretended to understand something I didn't.",
            "Never have I ever had a crush on someone I shouldn't.",
            "Never have I ever laughed at the worst possible moment.",
        ]
        await interaction.response.send_message(f"🙈 **{random.choice(prompts)}**")

    @bot.tree.command(name="thisorthat", description="Get a This or That choice")
    async def thisorthat(interaction: discord.Interaction):
        pairs = [
            ("Night", "Morning"), ("Beach", "Mountains"), ("Texting", "Calling"),
            ("Sweet", "Spicy"), ("Movies", "Series"), ("Cats", "Dogs"),
        ]
        a, b = random.choice(pairs)
        await interaction.response.send_message(f"⚡ **{a} or {b}?**")

    @bot.tree.command(name="daily", description="Get Shade's daily prompt")
    async def daily(interaction: discord.Interaction):
        prompts = [
            "What's one thing you want to accomplish today?",
            "What's something you're grateful for today?",
            "What's one thing you should stop putting off?",
            "What's one thing that would make today better?",
            "What's something you want to remember about today?",
        ]
        await interaction.response.send_message(f"🌅 **Daily prompt:** {random.choice(prompts)}")

    @bot.tree.command(name="shadecontrol", description="Owner-only Shade controls")
    @app_commands.describe(action="Control action")
    @app_commands.choices(action=[
        app_commands.Choice(name="Status", value="status"),
        app_commands.Choice(name="Personality", value="personality"),
    ])
    async def shadecontrol(interaction: discord.Interaction, action: app_commands.Choice[str]):
        if not _owner_only(interaction):
            return await interaction.response.send_message("❌ Owner only.", ephemeral=True)
        if action.value == "status":
            await interaction.response.send_message("🌑 Shade is online and running.", ephemeral=True)
        else:
            await interaction.response.send_message(
                "🖤 Personality: personal, playful, direct, and built around its owner.",
                ephemeral=True,
            )

    asyncio.create_task(_reminder_loop(bot))
