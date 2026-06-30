import asyncio
from datetime import datetime

import discord

from config import get_server
from ib import IBJoinView


class ReminderEngine:

    def __init__(self, bot):
        self.bot = bot
        self.sent = set()

    async def start(self):

        await self.bot.wait_until_ready()
        print("✅ Reminder engine started")

        while not self.bot.is_closed():

            try:
                await self.check_frost()
                await self.check_ib()

            except Exception as e:
                print(f"[Reminder Error] {e}")

            await asyncio.sleep(60)

    async def check_frost(self):

        today = datetime.now().strftime("%Y-%m-%d")
        now = datetime.now().strftime("%H:%M")

        print(f"Today: {today}")
        print(f"Now: {now}")

        for guild in self.bot.guilds:

            config = get_server(guild.id)

            channel_id = config.get("reminder_channel")

            if not channel_id:
                continue

            channel = guild.get_channel(channel_id)

            if channel is None:
                continue

            role = discord.utils.get(
                guild.roles,
                name="Frost"
            )

            for event in config.get("frost", []):

                if event["date"] != today:
                    continue

                if event["time"] != now:
                    continue

                key = (
                    guild.id,
                    "Frost",
                    event["city"],
                    event["date"],
                    event["time"]
                )

                if key in self.sent:
                    continue

                self.sent.add(key)

                mention = role.mention if role else "@everyone"

                embed = discord.Embed(
                    title="❄ Frost Reminder",
                    color=discord.Color.blue()
                )

                embed.add_field(
                    name="City",
                    value=event["city"],
                    inline=False
                )

                embed.add_field(
                    name="Date",
                    value=event["date"],
                    inline=True
                )

                embed.add_field(
                    name="Time",
                    value=event["time"],
                    inline=True
                )

                await channel.send(
                    content=mention,
                    embed=embed
                )

    async def check_ib(self):

        today = datetime.now().strftime("%Y-%m-%d")
        now = datetime.now().strftime("%H:%M")

        for guild in self.bot.guilds:

            config = get_server(guild.id)

            channel_id = config.get("reminder_channel")

            if not channel_id:
                continue

            channel = guild.get_channel(channel_id)

            if channel is None:
                continue

            role = discord.utils.get(
                guild.roles,
                name="IB"
            )

            for event in config.get("ib", []):

                if event["date"] != today:
                    continue

                if event["time"] != now:
                    continue

                key = (
                    guild.id,
                    "IB",
                    event["date"],
                    event["time"]
                )

                if key in self.sent:
                    continue

                self.sent.add(key)

                mention = role.mention if role else "@everyone"

                embed = discord.Embed(
                    title="🏰 IB Reminder",
                    color=discord.Color.green()
                )

                embed.add_field(
                    name="Date",
                    value=event["date"],
                    inline=True
                )

                embed.add_field(
                    name="Time",
                    value=event["time"],
                    inline=True
                )

                embed.add_field(
                    name="Notes",
                    value=event["notes"],
                    inline=False
                )

                await channel.send(
                    content=mention,
                    embed=embed,
                    view=IBJoinView()
                )


def setup(bot):
    engine = ReminderEngine(bot)

    @bot.listen()
    async def on_ready():
        if not hasattr(bot, "_reminder_started"):
            bot._reminder_started = True
            asyncio.create_task(engine.start())