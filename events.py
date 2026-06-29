import discord
from discord import app_commands

from config import get_server, save_server


class Frost(app_commands.Group):

    def __init__(self):
        super().__init__(
            name="frost",
            description="Frost event commands"
        )

    @app_commands.command(
        name="create",
        description="Create a Frost event"
    )
    @app_commands.describe(
        city="Frost city",
        time="Example: 20:00"
    )
    async def create(
        self,
        interaction: discord.Interaction,
        city: str,
        time: str
    ):

        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True
            )
            return

        config = get_server(interaction.guild.id)

        config["frost"].append(
            {
                "city": city,
                "time": time
            }
        )

        save_server()

        await interaction.response.send_message(
            f"✅ Frost event created!\n"
            f"❄ City: **{city}**\n"
            f"🕒 Time: **{time}**"
        )

    @app_commands.command(
        name="list",
        description="List all Frost events"
    )
    async def list(
        self,
        interaction: discord.Interaction
    ):

        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True
            )
            return

        config = get_server(interaction.guild.id)

        frost = config.get("frost", [])

        if not frost:
            await interaction.response.send_message(
                "❄ No Frost events found."
            )
            return

        embed = discord.Embed(
            title="❄ Frost Events",
            color=discord.Color.blue()
        )

        for index, event in enumerate(frost, start=1):

            embed.add_field(
                name=f"{index}. {event['city']}",
                value=f"🕒 {event['time']}",
                inline=False
            )

        await interaction.response.send_message(
            embed=embed
        )

    @app_commands.command(
        name="delete",
        description="Delete a Frost event"
    )
    @app_commands.describe(
        number="Event number from /frost list"
    )
    async def delete(
        self,
        interaction: discord.Interaction,
        number: int
    ):

        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True
            )
            return

        config = get_server(interaction.guild.id)

        frost = config.get("frost", [])

        if number < 1 or number > len(frost):
            await interaction.response.send_message(
                "❌ Invalid event number."
            )
            return

        removed = frost.pop(number - 1)

        save_server()

        await interaction.response.send_message(
            f"🗑 Deleted **{removed['city']}** ({removed['time']})"
        )
    @app_commands.command(
        name="clear",
        description="Delete all Frost events"
    )
    async def clear(
        self,
        interaction: discord.Interaction
    ):

        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True
            )
            return

        config = get_server(interaction.guild.id)

        config["frost"] = []

        save_server()

        await interaction.response.send_message(
            "🧹 All Frost events have been deleted."
        )


    @app_commands.command(
        name="edit",
        description="Edit a Frost event"
    )
    @app_commands.describe(
        number="Event number from /frost list",
        city="New city name",
        time="New time (Example: 20:00)"
    )
    async def edit(
        self,
        interaction: discord.Interaction,
        number: int,
        city: str,
        time: str
    ):

        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True
            )
            return

        config = get_server(interaction.guild.id)

        frost = config.get("frost", [])

        if number < 1 or number > len(frost):
            await interaction.response.send_message(
                "❌ Invalid event number."
            )
            return

        frost[number - 1]["city"] = city
        frost[number - 1]["time"] = time

        save_server()

        await interaction.response.send_message(
            f"✏️ Frost event #{number} updated.\n"
            f"❄ City: **{city}**\n"
            f"🕒 Time: **{time}**"
        )


def setup(bot):
    bot.tree.add_command(Frost())