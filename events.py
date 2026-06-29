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
        description="Create a Frost reminder"
    )
    @app_commands.describe(
        city="Frost city name",
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
                "❌ Server only.",
                ephemeral=True
            )
            return

        config = get_server(interaction.guild.id)

        config["frost"].append({
            "city": city,
            "time": time
        })

        save_server()

        await interaction.response.send_message(
            f"❄ Frost added!\n"
            f"City: **{city}**\n"
            f"Time: **{time}**"
        )

    @app_commands.command(
        name="list",
        description="Show all Frost events"
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
                value=f"Time: {event['time']}",
                inline=False
            )

        await interaction.response.send_message(
            embed=embed
        )


def setup(bot):
    bot.tree.add_command(Frost())