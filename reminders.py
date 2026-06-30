import asyncio
from datetime import datetime

import discord

from config import get_server


class ReminderEngine:

    def __init__(self, bot):
        self.bot = bot
        self.sent = set()

    async def start(self):

        await self.bot.wait_until_ready()

        while not self.bot.is_closed():

            try:
                await self.check_frost()

            except Exception as e:
                print(f"[Reminder Error] {e}")

            await asyncio.sleep(60)

    async def check_frost(self):

        today = datetime.now().strftime("%Y-%m-%d")
        now = datetime.now().strftime("%H:%M")

        for guild in self.bot.guilds:

            config = get_server(guild.id)

            channel_id = config.get("reminder_channel")
            role_id = config.get("ping_role")

            if not channel_id:
                continue

            channel = guild.get_channel(channel_id)

            if channel is None:
                continue

            role = guild.get_role(role_id) if role_id else None

            for event in config.get("frost", []):

                if event["date"] != today:
                    continue

                if event["time"] != now:
                    continue

                key = (
                    guild.id,
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


def setup(bot):
    engine = ReminderEngine(bot)

    @bot.event
    async def on_ready():
        bot.loop.create_task(engine.start())