import discord
from discord import app_commands

from config import get_server, save_server
from permissions import is_leadership


class Malena(app_commands.Group):

    def __init__(self):
        super().__init__(
            name="malena",
            description="Malena event commands"
        ) 

    @app_commands.command(
        name="create",
        description="Create a Malena event"
    )
    @app_commands.describe(
        date="YYYY-MM-DD",
        time="HH:MM",
        difficulty="Malena difficulty",
        notes="Optional notes"
    )
    async def create(
        self,
        interaction: discord.Interaction,
        date: str,
        time: str,
        difficulty: str,
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

        if "malena" not in config:
            config["malena"] = []

        config["malena"].append(
            {
                "date": date,
                "time": time,
                "difficulty": difficulty,
                "notes": notes
            }
        )

        save_server()

        channel_id = config.get("malena_channel")

        if channel_id:

            channel = interaction.guild.get_channel(channel_id)

            if channel:

                role = discord.utils.get(
                    interaction.guild.roles,
                    name="Malena"
                )

                mention = role.mention if role else "@everyone"

                embed = discord.Embed(
                    title="👑 Malena",
                    color=discord.Color.magenta()
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
                    name="⚔️ Difficulty",
                    value=difficulty,
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
            "✅ Malena event created successfully.",
            ephemeral=True
        ) 

    @app_commands.command(
        name="list",
        description="List all Malena events"
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

        events = config.get("malena", [])

        if not events:

            await interaction.response.send_message(
                "👑 No Malena events found."
            )
            return

        embed = discord.Embed(
            title="👑 Malena Events",
            color=discord.Color.magenta()
        )

        for index, event in enumerate(events, start=1):

            embed.add_field(
                name=f"{index}. Malena",
                value=(
                    f"📅 Date: {event['date']}\n"
                    f"🕒 Time: {event['time']}\n"
                    f"⚔️ Difficulty: {event['difficulty']}\n"
                    f"📝 {event['notes']}"
                ),
                inline=False
            )

        await interaction.response.send_message(
            embed=embed
        )

    @app_commands.command(
        name="edit",
        description="Edit a Malena event"
    )
    @app_commands.describe(
        number="Event number from /malena list",
        date="YYYY-MM-DD",
        time="HH:MM",
        difficulty="Malena difficulty",
        notes="Optional notes"
    )
    async def edit(
        self,
        interaction: discord.Interaction,
        number: int,
        date: str,
        time: str,
        difficulty: str,
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

        events = config.get("malena", [])

        if number < 1 or number > len(events):

            await interaction.response.send_message(
                "❌ Invalid event number.",
                ephemeral=True
            )
            return

        event = events[number - 1]

        event["date"] = date
        event["time"] = time
        event["difficulty"] = difficulty
        event["notes"] = notes

        save_server()

        await interaction.response.send_message(
            f"✏️ Malena event #{number} updated!\n"
            f"📅 Date: **{date}**\n"
            f"🕒 Time: **{time}**\n"
            f"⚔️ Difficulty: **{difficulty}**\n"
            f"📝 Notes: **{notes}**"
        ) 
 
    @app_commands.command(
        name="delete",
        description="Delete a Malena event"
    )
    @app_commands.describe(
        number="Event number from /malena list"
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

        events = config.get("malena", [])

        if number < 1 or number > len(events):

            await interaction.response.send_message(
                "❌ Invalid event number.",
                ephemeral=True
            )
            return

        removed = events.pop(number - 1)

        save_server()

        await interaction.response.send_message(
            f"🗑 Deleted Malena event "
            f"({removed['date']} {removed['time']})"
        )

    @app_commands.command(
        name="clear",
        description="Delete all Malena events"
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

        config["malena"] = []

        save_server()

        await interaction.response.send_message(
            "🧹 All Malena events have been deleted."
        )


def setup(bot):

    try:
        bot.tree.add_command(Malena())
    except Exception:
        pass