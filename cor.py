import discord
from discord import app_commands

from config import get_server, save_server
from permissions import is_leadership


class COR(app_commands.Group):

    def __init__(self):
        super().__init__(
            name="cor",
            description="Contention of Relics commands"
        ) 

    @app_commands.command(
        name="create",
        description="Create a Contention of Relics event"
    )
    @app_commands.describe(
        date="YYYY-MM-DD",
        time="HH:MM",
        relic="Relic name",
        node_level="Node level",
        notes="Optional notes"
    )
    async def create(
        self,
        interaction: discord.Interaction,
        date: str,
        time: str,
        relic: str,
        node_level: int,
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

        if "cor" not in config:
            config["cor"] = []

        config["cor"].append(
            {
                "date": date,
                "time": time,
                "relic": relic,
                "node_level": node_level,
                "notes": notes
            }
        )

        save_server()

        channel_id = config.get("cor_channel")

        if channel_id:

            channel = interaction.guild.get_channel(channel_id)

            if channel:

                role = discord.utils.get(
                    interaction.guild.roles,
                    name="CoR"
                )

                mention = role.mention if role else "@everyone"

                embed = discord.Embed(
                    title="🗿 Contention of Relics",
                    color=discord.Color.dark_purple()
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
                    name="🗿 Relic",
                    value=relic,
                    inline=True
                )

                embed.add_field(
                    name="⭐ Node Level",
                    value=str(node_level),
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
            "✅ Contention of Relics event created successfully.",
            ephemeral=True
        ) 
 
    @app_commands.command(
        name="list",
        description="List all Contention of Relics events"
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

        events = config.get("cor", [])

        if not events:

            await interaction.response.send_message(
                "🗿 No Contention of Relics events found."
            )
            return

        embed = discord.Embed(
            title="🗿 Contention of Relics Events",
            color=discord.Color.dark_purple()
        )

        for index, event in enumerate(events, start=1):

            embed.add_field(
                name=f"{index}. {event['relic']}",
                value=(
                    f"📅 Date: {event['date']}\n"
                    f"🕒 Time: {event['time']}\n"
                    f"⭐ Node Level: {event['node_level']}\n"
                    f"📝 {event['notes']}"
                ),
                inline=False
            )

        await interaction.response.send_message(
            embed=embed
        )

    @app_commands.command(
        name="edit",
        description="Edit a Contention of Relics event"
    )
    @app_commands.describe(
        number="Event number from /cor list",
        date="YYYY-MM-DD",
        time="HH:MM",
        relic="Relic name",
        node_level="Node level",
        notes="Optional notes"
    )
    async def edit(
        self,
        interaction: discord.Interaction,
        number: int,
        date: str,
        time: str,
        relic: str,
        node_level: int,
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

        events = config.get("cor", [])

        if number < 1 or number > len(events):

            await interaction.response.send_message(
                "❌ Invalid event number.",
                ephemeral=True
            )
            return

        event = events[number - 1]

        event["date"] = date
        event["time"] = time
        event["relic"] = relic
        event["node_level"] = node_level
        event["notes"] = notes

        save_server()

        await interaction.response.send_message(
            f"✏️ Contention of Relics event #{number} updated!\n"
            f"📅 Date: **{date}**\n"
            f"🕒 Time: **{time}**\n"
            f"🗿 Relic: **{relic}**\n"
            f"⭐ Node Level: **{node_level}**\n"
            f"📝 Notes: **{notes}**"
        )   

    @app_commands.command(
        name="delete",
        description="Delete a Contention of Relics event"
    )
    @app_commands.describe(
        number="Event number from /cor list"
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

        events = config.get("cor", [])

        if number < 1 or number > len(events):

            await interaction.response.send_message(
                "❌ Invalid event number.",
                ephemeral=True
            )
            return

        removed = events.pop(number - 1)

        save_server()

        await interaction.response.send_message(
            f"🗑 Deleted Contention of Relics event "
            f"({removed['relic']} | {removed['date']} {removed['time']})"
        )

    @app_commands.command(
        name="clear",
        description="Delete all Contention of Relics events"
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

        config["cor"] = []

        save_server()

        await interaction.response.send_message(
            "🧹 All Contention of Relics events have been deleted."
        )


def setup(bot):

    try:
        bot.tree.add_command(COR())
    except Exception:
        pass