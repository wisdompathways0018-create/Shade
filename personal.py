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
    profile.setdefault("bio", "Quiet mind. Sharp edge. Built different. I keep my circle small, my standards high, and my path my own. 🌑")
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

    # Game rounds are channel-scoped. Multiple people can answer the same
    # question, but only one next question is generated after a short window.
    game_rounds = {"wyr": {}, "nhie": {}}
    GAME_ANSWER_WINDOW = 8.0

    def _next_game_prompt(kind: str, channel_id: int, prompts: list):
        """Return a prompt without repeating until the channel's pool is exhausted."""
        state = game_rounds[kind].setdefault(
            channel_id,
            {"message_id": None, "task": None, "remaining": []},
        )
        if not state["remaining"]:
            state["remaining"] = list(range(len(prompts)))
            random.shuffle(state["remaining"])
        return prompts[state["remaining"].pop()]

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

    WYR_PROMPTS = [
        ["Would you rather have unlimited money or unlimited free time?","Unlimited money","Unlimited free time"],
        ["Would you rather read minds or become invisible?","Read minds","Become invisible"],
        ["Would you rather pause time or rewind time?","Pause time","Rewind time"],
        ["Would you rather be famous for your talent or respected for your character?","Famous for my talent","Respected for my character"],
        ["Would you rather have your dream house or your dream car?","Dream house","Dream car"],
        ["Would you rather always know when someone is lying or always know when someone is telling the truth?","Know when someone is lying","Know when someone is telling the truth"],
        ["Would you rather live by the ocean or in the mountains?","Ocean","Mountains"],
        ["Would you rather have one best friend or a hundred good friends?","One best friend","A hundred good friends"],
        ["Would you rather travel anywhere instantly or never need to sleep?","Travel instantly","Never need to sleep"],
        ["Would you rather be able to fly or breathe underwater?","Fly","Breathe underwater"],
        ["Would you rather have perfect memory or perfect focus?","Perfect memory","Perfect focus"],
        ["Would you rather always be lucky or always be prepared?","Always lucky","Always prepared"],
        ["Would you rather speak every language or play every instrument?","Every language","Every instrument"],
        ["Would you rather live without music or without movies?","No music","No movies"],
        ["Would you rather be able to teleport or time travel?","Teleport","Time travel"],
        ["Would you rather have a personal chef or a personal driver?","Personal chef","Personal driver"],
        ["Would you rather never use social media again or never watch TV again?","No social media","No TV"],
        ["Would you rather have unlimited pizza or unlimited ice cream?","Unlimited pizza","Unlimited ice cream"],
        ["Would you rather always win arguments or never get into arguments?","Always win","Never argue"],
        ["Would you rather be the smartest person in the room or the funniest?","Smartest","Funniest"],
        ["Would you rather have a rewind button for life or a pause button?","Rewind","Pause"],
        ["Would you rather know your future or change your past?","Know my future","Change my past"],
        ["Would you rather be rich and anonymous or famous and comfortable?","Rich and anonymous","Famous and comfortable"],
        ["Would you rather live in a city or a quiet village?","City","Quiet village"],
        ["Would you rather have your dream job or your dream relationship?","Dream job","Dream relationship"],
        ["Would you rather never feel tired or never feel stressed?","Never tired","Never stressed"],
        ["Would you rather always have perfect weather or perfect health?","Perfect weather","Perfect health"],
        ["Would you rather be able to talk to animals or speak every human language?","Talk to animals","Speak every language"],
        ["Would you rather have unlimited books or unlimited movies?","Unlimited books","Unlimited movies"],
        ["Would you rather be an amazing singer or an amazing dancer?","Amazing singer","Amazing dancer"],
        ["Would you rather always know what to say or always know what to do?","Know what to say","Know what to do"],
        ["Would you rather have a photographic memory or never forget a face?","Photographic memory","Never forget a face"],
        ["Would you rather be able to control fire or water?","Fire","Water"],
        ["Would you rather live in summer forever or winter forever?","Summer","Winter"],
        ["Would you rather have a private island or a luxury apartment?","Private island","Luxury apartment"],
        ["Would you rather be a famous athlete or famous musician?","Athlete","Musician"],
        ["Would you rather never have homework or never have chores?","No homework","No chores"],
        ["Would you rather always get the best seat or skip every line?","Best seat","Skip lines"],
        ["Would you rather have unlimited clothes or unlimited shoes?","Unlimited clothes","Unlimited shoes"],
        ["Would you rather be able to see one day into the future or one year into the past?","See tomorrow","See one year ago"],
        ["Would you rather have perfect confidence or perfect discipline?","Confidence","Discipline"],
        ["Would you rather be able to duplicate yourself or become invisible?","Duplicate myself","Invisible"],
        ["Would you rather always be ten minutes early or twenty minutes late?","Ten minutes early","Twenty minutes late"],
        ["Would you rather have a home in the city or a home in the countryside?","City home","Country home"],
        ["Would you rather never lose your phone or never lose your wallet?","Never lose phone","Never lose wallet"],
        ["Would you rather have a lifetime supply of your favorite food or drink?","Favorite food","Favorite drink"],
        ["Would you rather be able to instantly learn any skill or instantly master any sport?","Learn any skill","Master any sport"],
        ["Would you rather have a robot assistant or a flying car?","Robot assistant","Flying car"],
        ["Would you rather be able to control your dreams or never need to dream?","Control dreams","Never dream"],
        ["Would you rather have an extra hour every day or an extra day every month?","Extra hour daily","Extra day monthly"],
        ["Would you rather always have perfect Wi-Fi or perfect battery life?","Perfect Wi-Fi","Perfect battery"],
        ["Would you rather be able to breathe in space or survive underwater forever?","Breathe in space","Survive underwater"],
        ["Would you rather be extremely lucky or extremely talented?","Lucky","Talented"],
        ["Would you rather have a huge house or a huge bank account?","Huge house","Huge bank account"],
        ["Would you rather never need coffee or never need sleep?","No coffee needed","No sleep needed"],
        ["Would you rather have dinner with your favorite fictional character or favorite celebrity?","Fictional character","Celebrity"],
        ["Would you rather always have the perfect comeback or always make people laugh?","Perfect comeback","Make people laugh"],
        ["Would you rather be able to erase one embarrassing memory or relive one amazing memory?","Erase embarrassment","Relive amazing memory"],
        ["Would you rather have unlimited travel or unlimited shopping?","Unlimited travel","Unlimited shopping"],
        ["Would you rather be a great leader or a great teammate?","Great leader","Great teammate"],
        ["Would you rather always be able to find what you need or never lose anything?","Find anything","Never lose anything"],
        ["Would you rather have a photographic imagination or perfect musical hearing?","Photographic imagination","Perfect musical hearing"],
        ["Would you rather live without games or without music?","No games","No music"],
        ["Would you rather have a month-long vacation or four long weekends every month?","Month vacation","Four long weekends"],
        ["Would you rather always get the truth or always get a second chance?","Always get truth","Always get second chance"],
        ["Would you rather be able to change your appearance or your voice at will?","Change appearance","Change voice"],
        ["Would you rather have unlimited energy or unlimited patience?","Unlimited energy","Unlimited patience"],
        ["Would you rather be great at every sport or every video game?","Every sport","Every video game"],
        ["Would you rather always have perfect timing or perfect luck?","Perfect timing","Perfect luck"],
        ["Would you rather be able to remember every dream or control every dream?","Remember dreams","Control dreams"],
        ["Would you rather have a house with a pool or a house with a huge library?","Pool","Library"],
        ["Would you rather never have to wait or never have to rush?","Never wait","Never rush"],
        ["Would you rather have the ability to fix anything or build anything?","Fix anything","Build anything"],
        ["Would you rather always have your favorite meal available or your favorite song available live?","Favorite meal","Favorite song live"],
        ["Would you rather be able to make anyone smile or make anyone feel calm?","Make them smile","Make them calm"],
        ["Would you rather be known for kindness or creativity?","Kindness","Creativity"],
        ["Would you rather have unlimited storage on your phone or unlimited internet speed?","Unlimited storage","Unlimited speed"],
        ["Would you rather live in the past for a year or the future for a year?","Past","Future"],
        ["Would you rather have a private movie theater or private gaming room?","Movie theater","Gaming room"],
        ["Would you rather always have your favorite person nearby or your favorite place nearby?","Favorite person","Favorite place"],
        ["Would you rather be able to instantly solve any puzzle or instantly learn any language?","Solve puzzles","Learn languages"],
        ["Would you rather have perfect balance or perfect coordination?","Perfect balance","Perfect coordination"],
        ["Would you rather be able to stop bad habits instantly or start good habits instantly?","Stop bad habits","Start good habits"],
        ["Would you rather have unlimited confidence or unlimited motivation?","Confidence","Motivation"],
        ["Would you rather always know the right decision or always have someone you trust to advise you?","Know the decision","Trusted adviser"],
        ["Would you rather have a life full of surprises or a life fully planned?","Surprises","Fully planned"],
        ["Would you rather be able to change one rule of society or one rule of nature?","Society","Nature"],
        ["Would you rather have an endless summer vacation or endless weekends?","Summer vacation","Endless weekends"],
        ["Would you rather always have a clean room or a charged phone?","Clean room","Charged phone"],
        ["Would you rather be the funniest person or the most interesting person?","Funniest","Most interesting"],
        ["Would you rather have unlimited data or unlimited battery?","Unlimited data","Unlimited battery"],
        ["Would you rather be able to see your future career or future home?","Future career","Future home"],
        ["Would you rather have a personal trainer or personal tutor?","Personal trainer","Personal tutor"],
        ["Would you rather always get your favorite seat or your favorite meal?","Favorite seat","Favorite meal"],
        ["Would you rather have perfect handwriting or perfect typing speed?","Handwriting","Typing speed"],
        ["Would you rather always have fresh clothes or fresh food?","Fresh clothes","Fresh food"],
        ["Would you rather be able to shrink or grow at will?","Shrink","Grow"],
        ["Would you rather have a door to anywhere or a button that grants one wish each year?","Door anywhere","One wish yearly"],
        ["Would you rather never get bored or never get distracted?","Never bored","Never distracted"],
        ["Would you rather have unlimited creativity or unlimited knowledge?","Creativity","Knowledge"],
        ["Would you rather be able to fix your biggest mistake or guarantee your biggest success?","Fix mistake","Guarantee success"],
        ["Would you rather have your own theme park or your own restaurant?","Theme park","Restaurant"],
        ["Would you rather be able to turn invisible for ten minutes a day or fly for ten minutes a day?","Invisible","Fly"],
        ["Would you rather always have the perfect playlist or perfect lighting?","Playlist","Lighting"],
        ["Would you rather have unlimited free books or unlimited free games?","Books","Games"],
        ["Would you rather be able to talk to your future self or your past self?","Future self","Past self"],
        ["Would you rather have a perfect memory or a perfect imagination?","Memory","Imagination"],
        ["Would you rather always have a plan or always improvise?","Plan","Improvise"],
        ["Would you rather have unlimited snacks or unlimited drinks?","Snacks","Drinks"],
        ["Would you rather live near your friends or near your favorite places?","Friends","Favorite places"],
        ["Would you rather be able to master one skill instantly or improve every skill slowly?","Master one","Improve all"],
        ["Would you rather have an extra $100 every week or $5000 once?","$100 weekly","$5000 once"],
        ["Would you rather have a personal assistant or a personal chef?","Assistant","Chef"],
        ["Would you rather always have good hair or good skin?","Good hair","Good skin"],
        ["Would you rather never miss a bus or never wait for a bus?","Never miss","Never wait"],
        ["Would you rather have perfect pronunciation or perfect vocabulary?","Pronunciation","Vocabulary"],
        ["Would you rather always know where you left things or always remember names?","Find things","Remember names"],
        ["Would you rather have unlimited cloud storage or unlimited phone storage?","Cloud storage","Phone storage"],
        ["Would you rather spend a year traveling or a year building your dream project?","Travel","Dream project"],
        ["Would you rather be able to instantly decorate any room or instantly clean it?","Decorate","Clean"],
        ["Would you rather always have a great idea or always have the energy to execute it?","Great ideas","Energy"],
        ["Would you rather be able to replay any conversation or erase one conversation?","Replay","Erase"],
        ["Would you rather have perfect rhythm or perfect pitch?","Rhythm","Pitch"],
        ["Would you rather have an endless supply of your favorite dessert or snack?","Dessert","Snack"],
        ["Would you rather always be comfortable or always be challenged?","Comfort","Challenge"],
        ["Would you rather have a peaceful life or an exciting life?","Peaceful","Exciting"],
    ]

    def _wyr_content(channel_id: int):
        question, option_a, option_b = _next_game_prompt("wyr", channel_id, WYR_PROMPTS)
        return f"🤔 **Would You Rather?**\n\n{question}\n\n🅰️ **A:** {option_a}\n🅱️ **B:** {option_b}"

    async def _advance_wyr(channel, old_message_id: int):
        try:
            await asyncio.sleep(GAME_ANSWER_WINDOW)
            state = game_rounds["wyr"].get(channel.id)
            if (
                not state
                or state["message_id"] != old_message_id
                or not state.get("answer_started", False)
            ):
                return
            message = await channel.send(
                _wyr_content(channel.id),
                view=WouldYouRatherView(),
            )
            state["message_id"] = message.id
            state["task"] = None
            state["answer_started"] = False
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            print(f"❌ Would You Rather round advance failed: {exc}")

    class WouldYouRatherView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        async def _choose(self, interaction: discord.Interaction, choice: str):
            state = game_rounds["wyr"].get(interaction.channel_id)
            if not state or state["message_id"] != interaction.message.id:
                return await interaction.response.send_message(
                    "⚠️ That round has already moved on.", ephemeral=True
                )

            await interaction.response.defer()
            await interaction.followup.send(
                f"🤔 **<@{interaction.user.id}> chose {choice}!**"
            )

            state["answer_started"] = True
            task = state.get("task")
            if task is not None and not task.done():
                task.cancel()
            state["task"] = asyncio.create_task(
                _advance_wyr(interaction.channel, interaction.message.id)
            )

        @discord.ui.button(label="A", emoji="🅰️", style=discord.ButtonStyle.primary, custom_id="shade:wyr:a")
        async def option_a_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self._choose(interaction, "A")

        @discord.ui.button(label="B", emoji="🅱️", style=discord.ButtonStyle.secondary, custom_id="shade:wyr:b")
        async def option_b_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self._choose(interaction, "B")

    @bot.tree.command(name="wouldyourather", description="Start a Would You Rather game")
    async def wouldyourather(interaction: discord.Interaction):
        await interaction.response.send_message(_wyr_content(interaction.channel_id), view=WouldYouRatherView())
        message = await interaction.original_response()
        channel_id = interaction.channel_id
        previous = game_rounds["wyr"].get(channel_id)
        if previous and previous.get("task"):
            previous["task"].cancel()
        game_rounds["wyr"][channel_id] = {
            "message_id": message.id,
            "task": None,
            "answer_started": False,
            "remaining": game_rounds["wyr"].get(channel_id, {}).get("remaining", []),
        }

    NHIE_PROMPTS = [
        "Never have I ever lied about why I was late.",
        "Never have I ever stalked someone's social media.",
        "Never have I ever sent a message to the wrong person.",
        "Never have I ever pretended to understand something I didn't.",
        "Never have I ever had a crush on someone I shouldn't.",
        "Never have I ever laughed at the worst possible moment.",
        "Never have I ever stayed up all night for no good reason.",
        "Never have I ever deleted a message because I regretted sending it.",
        "Never have I ever forgotten someone's name right after meeting them.",
        "Never have I ever laughed when I was supposed to be serious.",
        "Never have I ever blamed someone else for something I did.",
        "Never have I ever sent a risky text and immediately regretted it.",
        "Never have I ever lied to get out of plans.",
        "Never have I ever eaten someone else's food without asking.",
        "Never have I ever pretended to be busy to avoid someone.",
        "Never have I ever rewatched a show instead of starting something new.",
        "Never have I ever forgotten a password.",
        "Never have I ever fallen asleep during a movie.",
        "Never have I ever sung loudly when nobody was listening.",
        "Never have I ever danced when I thought nobody was watching.",
        "Never have I ever accidentally liked an old post.",
        "Never have I ever deleted a message and hoped nobody noticed.",
        "Never have I ever sent a screenshot to the person I screenshotted.",
        "Never have I ever called someone by the wrong name.",
        "Never have I ever laughed at my own joke.",
        "Never have I ever practiced a conversation in my head.",
        "Never have I ever checked my phone even though I knew there were no notifications.",
        "Never have I ever ignored a message because I didn't know how to reply.",
        "Never have I ever pretended to know a song.",
        "Never have I ever watched an entire series in one day.",
        "Never have I ever stayed up late scrolling.",
        "Never have I ever bought something I didn't need.",
        "Never have I ever regretted a haircut.",
        "Never have I ever worn mismatched socks without noticing.",
        "Never have I ever forgotten someone's birthday.",
        "Never have I ever made an excuse to leave early.",
        "Never have I ever gotten lost somewhere familiar.",
        "Never have I ever talked to myself out loud.",
        "Never have I ever laughed at the wrong time.",
        "Never have I ever made a typo that changed the meaning of a message.",
        "Never have I ever sent a message and immediately turned off my phone.",
        "Never have I ever taken a photo and deleted it because it looked bad.",
        "Never have I ever pretended to understand a reference.",
        "Never have I ever forgotten why I walked into a room.",
        "Never have I ever eaten dessert before dinner.",
        "Never have I ever ordered the same thing because I couldn't decide.",
        "Never have I ever been embarrassed by an old photo.",
        "Never have I ever made a playlist for a very specific mood.",
        "Never have I ever used a fake excuse to cancel plans.",
        "Never have I ever stayed quiet because I didn't want to start an argument.",
        "Never have I ever accidentally spoiled a movie or show.",
        "Never have I ever searched my own name online.",
        "Never have I ever checked someone's profile more than once in a day.",
        "Never have I ever read a message without replying on purpose.",
        "Never have I ever forgotten where I parked.",
        "Never have I ever missed an alarm.",
        "Never have I ever set multiple alarms and ignored them all.",
        "Never have I ever eaten food after saying I wasn't hungry.",
        "Never have I ever taken the last piece without asking.",
        "Never have I ever pretended not to see someone in public.",
        "Never have I ever laughed because someone else was laughing.",
        "Never have I ever made a joke at the wrong time.",
        "Never have I ever practiced a facial expression in a mirror.",
        "Never have I ever talked myself into buying something.",
        "Never have I ever regretted sending a voice message.",
        "Never have I ever listened to the same song repeatedly.",
        "Never have I ever judged a book by its cover.",
        "Never have I ever watched the ending before the beginning.",
        "Never have I ever skipped an intro every single time.",
        "Never have I ever forgotten an important date.",
        "Never have I ever made plans and then hoped they got cancelled.",
        "Never have I ever said 'I'm fine' when I wasn't.",
        "Never have I ever pretended to be confident.",
        "Never have I ever changed my opinion because of the group.",
        "Never have I ever kept a secret longer than I expected.",
        "Never have I ever lost something while holding it.",
        "Never have I ever looked for my phone while holding it.",
        "Never have I ever opened the fridge without knowing what I wanted.",
        "Never have I ever forgotten someone's face after knowing their name.",
        "Never have I ever accidentally replied to the wrong chat.",
        "Never have I ever laughed during a serious conversation.",
        "Never have I ever used a nickname nobody else knew.",
        "Never have I ever made a promise I couldn't keep.",
        "Never have I ever procrastinated until the last minute.",
        "Never have I ever said 'five more minutes' and stayed longer.",
        "Never have I ever taken a nap that became a full sleep.",
        "Never have I ever worn the same outfit twice in a short period.",
        "Never have I ever forgotten something I was just told.",
        "Never have I ever changed my mind at the last second.",
        "Never have I ever avoided a call because I didn't want to talk.",
        "Never have I ever muted a group chat.",
        "Never have I ever left a group chat dramatically.",
        "Never have I ever joined a conversation without knowing the context.",
        "Never have I ever searched for an answer instead of figuring it out.",
        "Never have I ever pretended to be an expert.",
        "Never have I ever learned a word and immediately tried to use it.",
        "Never have I ever laughed at a meme more than once.",
        "Never have I ever sent a meme to the wrong person.",
        "Never have I ever forgotten to charge my phone.",
        "Never have I ever used someone else's charger without asking.",
        "Never have I ever lost an earbud.",
        "Never have I ever watched videos until sunrise.",
        "Never have I ever ignored a notification because I was too lazy to open it.",
        "Never have I ever refreshed an app repeatedly waiting for something.",
        "Never have I ever checked the time and immediately forgotten it.",
        "Never have I ever opened an app and forgotten why.",
        "Never have I ever made a typo in an important message.",
        "Never have I ever accidentally sent an unfinished message.",
        "Never have I ever deleted an app and reinstalled it later.",
        "Never have I ever taken a screenshot just to remember something.",
        "Never have I ever forgotten an umbrella and gotten caught in rain.",
        "Never have I ever worn headphones with nothing playing.",
        "Never have I ever pretended not to hear someone.",
        "Never have I ever overthought a simple text.",
        "Never have I ever reread my own message after sending it.",
        "Never have I ever changed a message because I worried how it sounded.",
        "Never have I ever stayed awake thinking about a conversation.",
        "Never have I ever made a decision based on a coin flip.",
        "Never have I ever lost track of time while gaming.",
        "Never have I ever started a game and played longer than planned.",
        "Never have I ever watched a trailer and spoiled the movie for myself.",
        "Never have I ever looked up a spoiler intentionally.",
        "Never have I ever skipped a difficult level and returned later.",
        "Never have I ever rage-quit a game.",
        "Never have I ever blamed lag for losing.",
        "Never have I ever made a dramatic exit from a conversation.",
        "Never have I ever apologized when I wasn't actually sorry.",
        "Never have I ever said yes just because everyone else did.",
        "Never have I ever said no and immediately regretted it.",
        "Never have I ever forgotten why I was annoyed.",
        "Never have I ever made a joke to hide embarrassment.",
        "Never have I ever smiled at my phone in public.",
        "Never have I ever accidentally opened the front camera.",
        "Never have I ever taken too many selfies before choosing one.",
        "Never have I ever deleted a post because it didn't get attention.",
        "Never have I ever checked who viewed something I posted.",
        "Never have I ever refreshed a page waiting for a reply.",
        "Never have I ever changed my status to match my mood.",
        "Never have I ever used an emoji to avoid answering.",
        "Never have I ever replied with just 'lol' because I had nothing to say.",
        "Never have I ever forgotten an appointment.",
        "Never have I ever arrived somewhere on the wrong day.",
        "Never have I ever confused two similar places.",
        "Never have I ever taken the wrong route.",
        "Never have I ever followed someone because I thought they were going the same way.",
        "Never have I ever asked for directions and still gotten lost.",
        "Never have I ever packed too much for a short trip.",
        "Never have I ever forgotten something important while traveling.",
        "Never have I ever fallen asleep during a journey.",
        "Never have I ever missed a stop because I was distracted.",
        "Never have I ever eaten snacks meant for later.",
        "Never have I ever bought snacks just because I was hungry.",
        "Never have I ever said I was full and kept eating.",
        "Never have I ever ordered food because someone else did.",
        "Never have I ever tried something just because a friend recommended it.",
        "Never have I ever disliked a popular food.",
        "Never have I ever loved a food everyone else disliked.",
        "Never have I ever changed my order after hearing someone else's order.",
        "Never have I ever taken a bite of someone else's food.",
        "Never have I ever forgotten to drink water all day.",
        "Never have I ever stayed in bed longer than planned.",
        "Never have I ever ignored a chore until someone reminded me.",
        "Never have I ever cleaned only because someone was coming over.",
        "Never have I ever hidden clutter instead of cleaning it.",
        "Never have I ever lost something because my room was messy.",
        "Never have I ever reorganized something instead of doing actual work.",
        "Never have I ever made a to-do list and ignored it.",
        "Never have I ever completed something early and felt surprised.",
        "Never have I ever rewarded myself before finishing the task.",
        "Never have I ever procrastinated by organizing something else.",
    ]

    def _nhie_content(channel_id: int):
        return f"🙈 **Never Have I Ever...**\n\n{_next_game_prompt('nhie', channel_id, NHIE_PROMPTS)}"

    async def _advance_nhie(channel, old_message_id: int):
        try:
            await asyncio.sleep(GAME_ANSWER_WINDOW)
            state = game_rounds["nhie"].get(channel.id)
            if (
                not state
                or state["message_id"] != old_message_id
                or not state.get("answer_started", False)
            ):
                return
            message = await channel.send(
                _nhie_content(channel.id),
                view=NeverHaveIEverView(),
            )
            state["message_id"] = message.id
            state["task"] = None
            state["answer_started"] = False
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            print(f"❌ Never Have I Ever round advance failed: {exc}")

    class NeverHaveIEverView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)

        async def _answer(self, interaction: discord.Interaction, answer: str):
            state = game_rounds["nhie"].get(interaction.channel_id)
            if not state or state["message_id"] != interaction.message.id:
                return await interaction.response.send_message(
                    "⚠️ That round has already moved on.", ephemeral=True
                )

            await interaction.response.defer()
            await interaction.followup.send(
                f"🙈 **<@{interaction.user.id}> says: {answer}!**"
            )

            task = state.get("task")
            if task is None or task.done():
                state["task"] = asyncio.create_task(
                    _advance_nhie(interaction.channel, interaction.message.id)
                )

        @discord.ui.button(label="I Have", emoji="🙋", style=discord.ButtonStyle.primary, custom_id="shade:nhie:have")
        async def have_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self._answer(interaction, "I Have")

        @discord.ui.button(label="Never", emoji="😇", style=discord.ButtonStyle.secondary, custom_id="shade:nhie:never")
        async def never_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self._answer(interaction, "Never")

    @bot.tree.command(name="neverhaveiever", description="Start a Never Have I Ever game")
    async def neverhaveiever(interaction: discord.Interaction):
        await interaction.response.send_message(_nhie_content(interaction.channel_id), view=NeverHaveIEverView())
        message = await interaction.original_response()
        channel_id = interaction.channel_id
        previous = game_rounds["nhie"].get(channel_id)
        if previous and previous.get("task"):
            previous["task"].cancel()
        game_rounds["nhie"][channel_id] = {
            "message_id": message.id,
            "task": None,
            "answer_started": False,
            "remaining": game_rounds["nhie"].get(channel_id, {}).get("remaining", []),
        }

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
    # Register persistent game buttons so they still work after a bot restart.
    bot.add_view(WouldYouRatherView())
    bot.add_view(NeverHaveIEverView())


def start_tasks(bot: commands.Bot):
    """Start Shade personal background tasks after the event loop is running."""
    return asyncio.create_task(_reminder_loop(bot))
