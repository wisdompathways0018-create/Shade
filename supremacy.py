import discord
from discord import app_commands

from config import get_server, save_server
from permissions import is_leadership


class Supremacy(app_commands.Group):

    def __init__(self):
        super().__init__(
            name="as",
            description="Alliance Supremacy commands"
        )

    @app_commands.command(
        name="create",
        description="Create an Alliance Supremacy event"
    )
    @app_commands.describe(
        date="YYYY-MM-DD",
        time="HH:MM",
        minimum_stp="Minimum STP required",
        notes="Optional notes"
    )
    async def create(
        self,
        interaction: discord.Interaction,
        date: str,
        time: str,
        minimum_stp: int,
        notes: str = "No notes"
    ):

        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Server only.",
                ephemeral=True
            )
            return

        if not is_leadership(interaction.user):
            await interaction.response.send_message(
                "❌ Only R5/R6 can use this command.",
                ephemeral=True
            )
            return

        config = get_server(interaction.guild.id)

        if "supremacy" not in config:
            config["supremacy"] = []

        config["supremacy"].append(
            {
                "date": date,
                "time": time,
                "minimum_stp": minimum_stp,
                "notes": notes
            }
        )

        save_server()

        channel_id = config.get("as_channel")

        if channel_id:

            channel = interaction.guild.get_channel(channel_id)

            if channel:

                role = discord.utils.get(
                    interaction.guild.roles,
                    name="Alliance Supremacy"
                )

                mention = role.mention if role else "@everyone"

                embed = discord.Embed(
                    title="🏆 Alliance Supremacy",
                    color=discord.Color.gold()
                )

                embed.add_field(
                    name="📅 Date",
                    value=date,
                    inline=True
                )

                embed.add_field(
                    name="🕒 Time",
                    value=time,
                    inline=True
                )

                embed.add_field(
                    name="⭐ Minimum STP",
                    value=f"{minimum_stp:,}",
                    inline=True
                )

                embed.add_field(
                    name="📝 Notes",
                    value=notes,
                    inline=False
                )

                await channel.send(
                    content=mention,
                    embed=embed
                )

        await interaction.response.send_message(
            "✅ Alliance Supremacy created successfully.",
            ephemeral=True
        )
    @app_commands.command(
            name="list",
            description="List all Alliance Supremacy events"
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

        if not is_leadership(interaction.user):
            await interaction.response.send_message(
                "❌ Only R5/R6 can use this command.",
                ephemeral=True
            )
            return

        config = get_server(interaction.guild.id)

        events = config.get("supremacy", [])

        if not events:
            await interaction.response.send_message(
                "🏆 No Alliance Supremacy events found."
            )
            return

        embed = discord.Embed(
            title="🏆 Alliance Supremacy Events",
            color=discord.Color.gold()
        )

        for index, event in enumerate(events, start=1):

            embed.add_field(
                name=f"{index}. Alliance Supremacy",
                value=(
                    f"📅 Date: {event['date']}\n"
                    f"🕒 Time: {event['time']}\n"
                    f"⭐ Minimum STP: {event['minimum_stp']:,}\n"
                    f"📝 {event['notes']}"
                ),
                inline=False
            )

        await interaction.response.send_message(
            embed=embed
        )

    @app_commands.command(
        name="edit",
        description="Edit an Alliance Supremacy event"
    )
    @app_commands.describe(
        number="Event number from /as list",
        date="YYYY-MM-DD",
        time="HH:MM",
        minimum_stp="Minimum STP required",
        notes="Optional notes"
    )
    async def edit(
        self,
        interaction: discord.Interaction,
        number: int,
        date: str,
        time: str,
        minimum_stp: int,
        notes: str = "No notes"
    ):

        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Server only.",
                ephemeral=True
            )
            return

        if not is_leadership(interaction.user):
            await interaction.response.send_message(
                "❌ Only R5/R6 can use this command.",
                ephemeral=True
            )
            return

        config = get_server(interaction.guild.id)

        events = config.get("supremacy", [])

        if number < 1 or number > len(events):

            await interaction.response.send_message(
                "❌ Invalid event number.",
                ephemeral=True
            )
            return

        event = events[number - 1]

        event["date"] = date
        event["time"] = time
        event["minimum_stp"] = minimum_stp
        event["notes"] = notes

        save_server()

        await interaction.response.send_message(
            f"✏️ Alliance Supremacy #{number} updated!\n"
            f"📅 Date: **{date}**\n"
            f"🕒 Time: **{time}**\n"
            f"⭐ Minimum STP: **{minimum_stp:,}**\n"
            f"📝 Notes: **{notes}**"
        )
    @app_commands.command(
            name="delete",
            description="Delete an Alliance Supremacy event"
    )
    @app_commands.describe(
        number="Event number from /as list"
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

        if not is_leadership(interaction.user):
            await interaction.response.send_message(
                "❌ Only R5/R6 can use this command.",
                ephemeral=True
            )
            return

        config = get_server(interaction.guild.id)

        events = config.get("supremacy", [])

        if number < 1 or number > len(events):

            await interaction.response.send_message(
                "❌ Invalid event number.",
                ephemeral=True
            )
            return

        removed = events.pop(number - 1)

        save_server()

        await interaction.response.send_message(
            f"🗑 Deleted Alliance Supremacy event "
            f"({removed['date']} {removed['time']})"
        )

    @app_commands.command(
        name="clear",
        description="Delete all Alliance Supremacy events"
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

        if not is_leadership(interaction.user):
            await interaction.response.send_message(
                "❌ Only R5/R6 can use this command.",
                ephemeral=True
            )
            return

        config = get_server(interaction.guild.id)

        config["supremacy"] = []

        save_server()

        await interaction.response.send_message(
            "🧹 All Alliance Supremacy events have been deleted."
        )


def setup(bot):

    try:
        bot.tree.add_command(Supremacy())
    except Exception:
        pass