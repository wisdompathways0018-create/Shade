import asyncio
from datetime import datetime, timedelta

import discord

from config import get_server


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
                await self.check_ke()
                await self.check_supremacy()
                await self.check_cor()
                await self.check_malena()

            except Exception as e:
                print(f"[Reminder Error] {e}")

            await asyncio.sleep(60)

    def reminder_type(
        self,
        event_date: str,
        event_time: str
    ):

        try:

            event_datetime = datetime.strptime(
                f"{event_date} {event_time}",
                "%Y-%m-%d %H:%M"
            )

        except Exception:
            return None

        now = datetime.now()

        diff = event_datetime - now

        if timedelta(minutes=59) <= diff <= timedelta(minutes=61):
            return "1 Hour"

        if timedelta(minutes=29) <= diff <= timedelta(minutes=31):
            return "30 Minutes"

        if timedelta(minutes=4) <= diff <= timedelta(minutes=6):
            return "5 Minutes"

        return None

    async def check_frost(self):

        for guild in self.bot.guilds:

            config = get_server(guild.id)

            channel_id = config.get("frost_channel")

            if not channel_id:
                continue

            channel = guild.get_channel(channel_id)

            if channel is None:
                continue

            role = discord.utils.get(
                guild.roles,
                name="Frost"
            )

            mention = role.mention if role else "@everyone"

            for event in config.get("frost", []):

                reminder = self.reminder_type(
                    event["date"],
                    event["time"]
                )

                if reminder is None:
                    continue

                key = (
                    guild.id,
                    "Frost",
                    event["city"],
                    event["date"],
                    event["time"],
                    reminder
                )

                if key in self.sent:
                    continue

                self.sent.add(key)

                embed = discord.Embed(
                    title=f"❄️ Frost Reminder ({reminder})",
                    color=discord.Color.blue()
                )

                embed.add_field(
                    name="🏰 City",
                    value=event["city"],
                    inline=False
                )

                embed.add_field(
                    name="📅 Date",
                    value=event["date"],
                    inline=True
                )

                embed.add_field(
                    name="🕒 Time",
                    value=event["time"],
                    inline=True
                )

                await channel.send(
                    content=mention,
                    embed=embed
                )  

    async def check_ib(self):

        for guild in self.bot.guilds:

            config = get_server(guild.id)

            channel_id = config.get("ib_channel")

            if not channel_id:
                continue

            channel = guild.get_channel(channel_id)

            if channel is None:
                continue

            role = discord.utils.get(
                guild.roles,
                name="IB"
            )

            mention = role.mention if role else "@everyone"

            for event in config.get("ib", []):

                reminder = self.reminder_type(
                    event["date"],
                    event["time"]
                )

                if reminder is None:
                    continue

                key = (
                    guild.id,
                    "IB",
                    event["date"],
                    event["time"],
                    reminder
                )

                if key in self.sent:
                    continue

                self.sent.add(key)

                embed = discord.Embed(
                    title=f"🏰 Iron Bastion Reminder ({reminder})",
                    color=discord.Color.green()
                )

                embed.add_field(
                    name="📅 Date",
                    value=event["date"],
                    inline=True
                )

                embed.add_field(
                    name="🕒 Time",
                    value=event["time"],
                    inline=True
                )

                embed.add_field(
                    name="📝 Notes",
                    value=event["notes"],
                    inline=False
                )

                await channel.send(
                    content=mention,
                    embed=embed
                )

    async def check_ke(self):

        for guild in self.bot.guilds:

            config = get_server(guild.id)

            channel_id = config.get("ke_channel")

            if not channel_id:
                continue

            channel = guild.get_channel(channel_id)

            if channel is None:
                continue

            mention = "@everyone"

            for event in config.get("ke", []):

                reminder = self.reminder_type(
                    event["start_date"],
                    "00:00"
                )

                if reminder is None:
                    continue

                key = (
                    guild.id,
                    "KE",
                    event["start_date"],
                    reminder
                )

                if key in self.sent:
                    continue

                self.sent.add(key)

                embed = discord.Embed(
                    title=f"⚔️ Kill Event Reminder ({reminder})",
                    color=discord.Color.red()
                )

                embed.add_field(
                    name="📅 Start Date",
                    value=event["start_date"],
                    inline=True
                )

                embed.add_field(
                    name="📅 End Date",
                    value=event["end_date"],
                    inline=True
                )

                embed.add_field(
                    name="📝 Notes",
                    value=event["notes"],
                    inline=False
                )

                await channel.send(
                    content=mention,
                    embed=embed
                ) 

    async def check_supremacy(self):

        for guild in self.bot.guilds:

            config = get_server(guild.id)

            channel_id = config.get("as_channel")

            if not channel_id:
                continue

            channel = guild.get_channel(channel_id)

            if channel is None:
                continue

            role = discord.utils.get(
                guild.roles,
                name="Alliance Supremacy"
            )

            mention = role.mention if role else "@everyone"

            for event in config.get("supremacy", []):

                reminder = self.reminder_type(
                    event["date"],
                    event["time"]
                )

                if reminder is None:
                    continue

                key = (
                    guild.id,
                    "Alliance Supremacy",
                    event["date"],
                    event["time"],
                    reminder
                )

                if key in self.sent:
                    continue

                self.sent.add(key)

                embed = discord.Embed(
                    title=f"🏆 Alliance Supremacy Reminder ({reminder})",
                    color=discord.Color.gold()
                )

                embed.add_field(
                    name="📅 Date",
                    value=event["date"],
                    inline=True
                )

                embed.add_field(
                    name="🕒 Time",
                    value=event["time"],
                    inline=True
                )

                embed.add_field(
                    name="⭐ Minimum STP",
                    value=f"{event['minimum_stp']:,}",
                    inline=True
                )

                embed.add_field(
                    name="📝 Notes",
                    value=event["notes"],
                    inline=False
                )

                await channel.send(
                    content=mention,
                    embed=embed
                )

    async def check_cor(self):

        for guild in self.bot.guilds:

            config = get_server(guild.id)

            channel_id = config.get("cor_channel")

            if not channel_id:
                continue

            channel = guild.get_channel(channel_id)

            if channel is None:
                continue

            mention = "@everyone"

            for event in config.get("cor", []):

                reminder = self.reminder_type(
                    event["date"],
                    event["time"]
                )

                if reminder is None:
                    continue

                key = (
                    guild.id,
                    "CoR",
                    event["relic"],
                    event["date"],
                    event["time"],
                    reminder
                )

                if key in self.sent:
                    continue

                self.sent.add(key)

                embed = discord.Embed(
                    title=f"🗿 Contention of Relics Reminder ({reminder})",
                    color=discord.Color.dark_purple()
                )

                embed.add_field(
                    name="🗿 Relic",
                    value=event["relic"],
                    inline=True
                )

                embed.add_field(
                    name="⭐ Node Level",
                    value=str(event["node_level"]),
                    inline=True
                )

                embed.add_field(
                    name="📅 Date",
                    value=event["date"],
                    inline=True
                )

                embed.add_field(
                    name="🕒 Time",
                    value=event["time"],
                    inline=True
                )

                embed.add_field(
                    name="📝 Notes",
                    value=event["notes"],
                    inline=False
                )

                await channel.send(
                    content=mention,
                    embed=embed
                )

    async def check_malena(self):

        for guild in self.bot.guilds:

            config = get_server(guild.id)

            channel_id = config.get("malena_channel")

            if not channel_id:
                continue

            channel = guild.get_channel(channel_id)

            if channel is None:
                continue

            mention = "@everyone"

            for event in config.get("malena", []):

                reminder = self.reminder_type(
                    event["date"],
                    event["time"]
                )

                if reminder is None:
                    continue

                key = (
                    guild.id,
                    "Malena",
                    event["date"],
                    event["time"],
                    reminder
                )

                if key in self.sent:
                    continue

                self.sent.add(key)

                embed = discord.Embed(
                    title=f"👑 Malena Reminder ({reminder})",
                    color=discord.Color.magenta()
                )

                embed.add_field(
                    name="📅 Date",
                    value=event["date"],
                    inline=True
                )

                embed.add_field(
                    name="🕒 Time",
                    value=event["time"],
                    inline=True
                )

                embed.add_field(
                    name="⚔️ Difficulty",
                    value=event["difficulty"],
                    inline=True
                )

                embed.add_field(
                    name="📝 Notes",
                    value=event["notes"],
                    inline=False
                )

                await channel.send(
                    content=mention,
                    embed=embed
                )


def setup(bot):

    engine = ReminderEngine(bot)

    @bot.listen()
    async def on_ready():

        if getattr(bot, "_reminder_started", False):
            return

        bot._reminder_started = True

        asyncio.create_task(
            engine.start()
        )