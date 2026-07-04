import discord
from discord import app_commands

from config import get_server, save_server
from permissions import is_leadership


class KE(app_commands.Group):

    def __init__(self):
        super().__init__(
            name="ke",
            description="Kill Event commands"
        )

    @app_commands.command(
        name="create",
        description="Create a Kill Event"
    )
    @app_commands.describe(
        start_date="YYYY-MM-DD",
        end_date="YYYY-MM-DD",
        notes="Optional notes"
    )
    async def create(
        self,
        interaction: discord.Interaction,
        start_date: str,
        end_date: str,
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

        if "ke" not in config:
            config["ke"] = []

        config["ke"].append(
            {
                "start_date": start_date,
                "end_date": end_date,
                "notes": notes
            }
        )

        save_server()

        channel_id = config.get("ke_channel")

        if channel_id:

            channel = interaction.guild.get_channel(channel_id)

            if channel:

                role = discord.utils.get(
                    interaction.guild.roles,
                    name="KE"
                )

                mention = role.mention if role else "@everyone"

                embed = discord.Embed(
                    title="⚔️ Kill Event",
                    color=discord.Color.red()
                )

                embed.add_field(
                    name="📅 Start Date",
                    value=start_date,
                    inline=True
                )

                embed.add_field(
                    name="📅 End Date",
                    value=end_date,
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
            "✅ Kill Event created successfully.",
            ephemeral=True
        )
    @app_commands.command(
            name="list",
            description="List all Kill Events"
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

        events = config.get("ke", [])

        if not events:
            await interaction.response.send_message(
                "⚔️ No Kill Events found."
            )
            return

        embed = discord.Embed(
            title="⚔️ Kill Events",
            color=discord.Color.red()
        )

        for index, event in enumerate(events, start=1):

            embed.add_field(
                name=f"{index}. Kill Event",
                value=(
                    f"📅 Start: {event['start_date']}\n"
                    f"📅 End: {event['end_date']}\n"
                    f"📝 {event['notes']}"
                ),
                inline=False
            )

        await interaction.response.send_message(
            embed=embed
        )

    @app_commands.command(
        name="edit",
        description="Edit a Kill Event"
    )
    @app_commands.describe(
        number="Event number from /ke list",
        start_date="YYYY-MM-DD",
        end_date="YYYY-MM-DD",
        notes="Optional notes"
    )
    async def edit(
        self,
        interaction: discord.Interaction,
        number: int,
        start_date: str,
        end_date: str,
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

        events = config.get("ke", [])

        if number < 1 or number > len(events):

            await interaction.response.send_message(
                "❌ Invalid event number.",
                ephemeral=True
            )
            return

        event = events[number - 1]

        event["start_date"] = start_date
        event["end_date"] = end_date
        event["notes"] = notes

        save_server()

        await interaction.response.send_message(
            f"✏️ Kill Event #{number} updated!\n"
            f"📅 Start: **{start_date}**\n"
            f"📅 End: **{end_date}**\n"
            f"📝 Notes: **{notes}**"
        )
    @app_commands.command(
            name="delete",
            description="Delete a Kill Event"
    )
    @app_commands.describe(
        number="Event number from /ke list"
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

        events = config.get("ke", [])

        if number < 1 or number > len(events):

            await interaction.response.send_message(
                "❌ Invalid event number.",
                ephemeral=True
            )
            return

        removed = events.pop(number - 1)

        save_server()

        await interaction.response.send_message(
            f"🗑 Deleted Kill Event "
            f"({removed['start_date']} → {removed['end_date']})"
        )

    @app_commands.command(
        name="clear",
        description="Delete all Kill Events"
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

        config["ke"] = []

        save_server()

        await interaction.response.send_message(
            "🧹 All Kill Events have been deleted."
        )


def setup(bot):

    try:
        bot.tree.add_command(KE())
    except Exception:
        pass