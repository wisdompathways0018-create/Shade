import discord
from discord import app_commands

from config import get_server, save_server


class IBJoinView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="✅ Join IB",
        style=discord.ButtonStyle.green
    )
    async def join(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_message(
            "Joining will be enabled in the next step.",
            ephemeral=True
        )

    @discord.ui.button(
        label="❌ Leave IB",
        style=discord.ButtonStyle.red
    )
    async def leave(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_message(
            "Leaving will be enabled in the next step.",
            ephemeral=True
        )



class IB(app_commands.Group):

    def __init__(self):
        super().__init__(
            name="ib",
            description="IB event commands"
        )

    @app_commands.command(
        name="create",
        description="Create an IB event"
    )
    @app_commands.describe(
        date="YYYY-MM-DD",
        time="HH:MM (UTC)",
        notes="Optional notes"
    )
    async def create(
        self,
        interaction: discord.Interaction,
        date: str,
        time: str,
        notes: str = "No notes"
    ):

        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Server only.",
                ephemeral=True
            )
            return

        config = get_server(interaction.guild.id)

        if "ib" not in config:
            config["ib"] = []

        config["ib"].append(
            {
                "date": date,
                "time": time,
                "notes": notes,
                "attendees": []
            }
        )

        save_server()

        await interaction.response.send_message(
            f"✅ IB event created!\n"
            f"📅 Date: **{date}**\n"
            f"🕒 Time: **{time}**\n"
            f"📝 Notes: **{notes}**"
        )

    @app_commands.command(
        name="list",
        description="List all IB events"
    )
    async def list(
        self,
        interaction: discord.Interaction
    ):

        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Server only.",
                ephemeral=True
            )
            return

        config = get_server(interaction.guild.id)

        events = config.get("ib", [])

        if not events:
            await interaction.response.send_message(
                "🏰 No IB events found."
            )
            return

        embed = discord.Embed(
            title="🏰 IB Events",
            color=discord.Color.green()
        )

        for index, event in enumerate(events, start=1):

            attendees = len(event.get("attendees", []))

            embed.add_field(
                name=f"{index}. IB Event",
                value=(
                    f"📅 {event['date']}\n"
                    f"🕒 {event['time']}\n"
                    f"📝 {event['notes']}\n"
                    f"👥 Attendees: **{attendees}**"
                ),
                inline=False
            )

        await interaction.response.send_message(
            embed=embed
        )

    @app_commands.command(
        name="delete",
        description="Delete an IB event"
    )
    @app_commands.describe(
        number="Event number from /ib list"
    )
    async def delete(
        self,
        interaction: discord.Interaction,
        number: int
    ):

        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Server only.",
                ephemeral=True
            )
            return

        config = get_server(interaction.guild.id)

        events = config.get("ib", [])

        if number < 1 or number > len(events):
            await interaction.response.send_message(
                "❌ Invalid event number."
            )
            return

        removed = events.pop(number - 1)

        save_server()

        await interaction.response.send_message(
            f"🗑 Deleted IB event "
            f"({removed['date']} {removed['time']})"
        )

    @app_commands.command(
        name="clear",
        description="Delete all IB events"
    )
    async def clear(
        self,
        interaction: discord.Interaction
    ):

        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Server only.",
                ephemeral=True
            )
            return

        config = get_server(interaction.guild.id)

        config["ib"] = []

        save_server()

        await interaction.response.send_message(
            "🧹 All IB events have been deleted."
        )

    @app_commands.command(
        name="edit",
        description="Edit an IB event"
    )
    @app_commands.describe(
        number="Event number from /ib list",
        date="YYYY-MM-DD",
        time="HH:MM (UTC)",
        notes="Optional notes"
    )
    async def edit(
        self,
        interaction: discord.Interaction,
        number: int,
        date: str,
        time: str,
        notes: str = "No notes"
    ):

        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Server only.",
                ephemeral=True
            )
            return

        config = get_server(interaction.guild.id)

        events = config.get("ib", [])

        if number < 1 or number > len(events):
            await interaction.response.send_message(
                "❌ Invalid event number."
            )
            return

        event = events[number - 1]

        event["date"] = date
        event["time"] = time
        event["notes"] = notes

        if "attendees" not in event:
            event["attendees"] = []

        save_server()

        await interaction.response.send_message(
            f"✏️ IB event #{number} updated!\n"
            f"📅 Date: **{date}**\n"
            f"🕒 Time: **{time}**\n"
            f"📝 Notes: **{notes}**"
        )


def setup(bot):
    bot.add_view(IBJoinView())
    bot.tree.add_command(IB())