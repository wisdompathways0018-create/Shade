import discord
from discord import app_commands

from config import get_server, save_server
from permissions import is_leadership


class IBJoinView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="✅ Join IB",
        style=discord.ButtonStyle.green,
        custom_id="ib_join"
    )
    async def join(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.guild is None:
            return

        config = get_server(interaction.guild.id)

        for event in config.get("ib", []):

            if event.get("message_id") != interaction.message.id:
                continue

            attendees = event.setdefault("attendees", [])

            if interaction.user.id in attendees:
                await interaction.response.send_message(
                    "✅ You have already joined this IB event.",
                    ephemeral=True
                )
                return

            attendees.append(interaction.user.id)
            save_server()

            member_lines = []

            for user_id in attendees:
                member = interaction.guild.get_member(user_id)

                if member:
                    member_lines.append(f"• {member.display_name}")

            members_text = (
                "\n".join(member_lines)
                if member_lines
                else "No one has joined yet."
            )

            embed = interaction.message.embeds[0].copy()

            embed.set_field_at(
                index=3,
                name="👥 Joined",
                value=str(len(attendees)),
                inline=False
            )

            embed.set_field_at(
                index=4,
                name="📋 Members",
                value=members_text,
                inline=False
            )

            await interaction.message.edit(
                embed=embed,
                view=self
            )

            await interaction.response.send_message(
                "✅ You joined this IB event.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "❌ Event not found.",
            ephemeral=True
        )

    @discord.ui.button(
        label="❌ Leave IB",
        style=discord.ButtonStyle.red,
        custom_id="ib_leave"
    )
    async def leave(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.guild is None:
            return

        config = get_server(interaction.guild.id)

        for event in config.get("ib", []):

            if event.get("message_id") != interaction.message.id:
                continue

            attendees = event.setdefault("attendees", [])

            if interaction.user.id not in attendees:
                await interaction.response.send_message(
                    "❌ You haven't joined this IB event.",
                    ephemeral=True
                )
                return

            attendees.remove(interaction.user.id)
            save_server()

            member_lines = []

            for user_id in attendees:
                member = interaction.guild.get_member(user_id)

                if member:
                    member_lines.append(f"• {member.display_name}")

            members_text = (
                "\n".join(member_lines)
                if member_lines
                else "No one has joined yet."
            )

            embed = interaction.message.embeds[0].copy()

            embed.set_field_at(
                index=3,
                name="👥 Joined",
                value=str(len(attendees)),
                inline=False
            )

            embed.set_field_at(
                index=4,
                name="📋 Members",
                value=members_text,
                inline=False
            )

            await interaction.message.edit(
                embed=embed,
                view=self
            )

            await interaction.response.send_message(
                "✅ You left this IB event.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "❌ Event not found.",
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

        if not is_leadership(interaction.user):
            await interaction.response.send_message(
                "❌ Only R5/R6 can use this command.",
                ephemeral=True
            )
            return

        config = get_server(interaction.guild.id)

        if "ib" not in config:
            config["ib"] = []

        event = {
            "date": date,
            "time": time,
            "notes": notes,
            "attendees": [],
            "message_id": None
        }

        config["ib"].append(event)
        save_server()

        channel_id = config.get("reminder_channel")

        if channel_id:

            channel = interaction.guild.get_channel(channel_id)

            if channel:

                role = discord.utils.get(
                    interaction.guild.roles,
                    name="IB"
                )

                mention = role.mention if role else "@everyone"

                embed = discord.Embed(
                    title="🏰 IB Event",
                    color=discord.Color.green()
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
                    name="📝 Notes",
                    value=notes,
                    inline=False
                )

                embed.add_field(
                    name="👥 Joined",
                    value="0",
                    inline=False
                )

                embed.add_field(
                    name="📋 Members",
                    value="No one has joined yet.",
                    inline=False
                )

                message = await channel.send(
                    content=mention,
                    embed=embed,
                    view=IBJoinView()
                )

                event["message_id"] = message.id
                save_server()

        await interaction.response.send_message(
            "✅ IB event created successfully.",
            ephemeral=True
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

        if not is_leadership(interaction.user):
            await interaction.response.send_message(
                "❌ Only R5/R6 can use this command.",
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

        if not is_leadership(interaction.user):
            await interaction.response.send_message(
                "❌ Only R5/R6 can use this command.",
                ephemeral=True
            )
            return

        config = get_server(interaction.guild.id)

        events = config.get("ib", [])

        if number < 1 or number > len(events):

            await interaction.response.send_message(
                "❌ Invalid event number.",
                ephemeral=True
            )
            return

        event = events[number - 1]

        event["date"] = date
        event["time"] = time
        event["notes"] = notes

        event.setdefault("attendees", [])
        event.setdefault("message_id", None)

        save_server()

        await interaction.response.send_message(
            f"✏️ IB event #{number} updated!\n"
            f"📅 Date: **{date}**\n"
            f"🕒 Time: **{time}**\n"
            f"📝 Notes: **{notes}**"
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

        if not is_leadership(interaction.user):
            await interaction.response.send_message(
                "❌ Only R5/R6 can use this command.",
                ephemeral=True
            )
            return

        config = get_server(interaction.guild.id)

        events = config.get("ib", [])

        if number < 1 or number > len(events):

            await interaction.response.send_message(
                "❌ Invalid event number.",
                ephemeral=True
            )
            return

        removed = events.pop(number - 1)

        save_server()

        await interaction.response.send_message(
            f"🗑 Deleted IB event ({removed['date']} {removed['time']})"
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

        if not is_leadership(interaction.user):
            await interaction.response.send_message(
                "❌ Only R5/R6 can use this command.",
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
        name="attendees",
        description="Show everyone who joined an IB event"
    )
    @app_commands.describe(
        number="Event number from /ib list"
    )
    async def attendees(
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
                "❌ Invalid event number.",
                ephemeral=True
            )
            return

        if not is_leadership(interaction.user):
            await interaction.response.send_message(
                "❌ Only R5/R6 can use this command.",
                ephemeral=True
            )
            return

        event = events[number - 1]

        attendees = event.get("attendees", [])

        embed = discord.Embed(
            title=f"🏰 IB Event #{number}",
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

        if attendees:

            names = []

            for user_id in attendees:

                member = interaction.guild.get_member(user_id)

                if member:
                    names.append(f"• {member.display_name}")

            embed.add_field(
                name=f"👥 Joined ({len(names)})",
                value="\n".join(names),
                inline=False
            )

        else:

            embed.add_field(
                name="👥 Joined",
                value="No members have joined yet.",
                inline=False
            )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


def setup(bot):

    bot.add_view(IBJoinView())

    try:
        bot.tree.add_command(IB())
    except Exception:
        pass