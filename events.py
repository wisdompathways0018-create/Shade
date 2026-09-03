import discord
from discord import app_commands

from config import get_server, save_server
from permissions import is_leadership


class Frost(app_commands.Group):

    def __init__(self):
        super().__init__(name="frost", description="Frost event commands")

    async def _leadership_only(self, interaction: discord.Interaction) -> bool:
        if interaction.guild is None:
            await interaction.response.send_message("❌ Server only.", ephemeral=True)
            return False
        if not is_leadership(interaction.user):
            await interaction.response.send_message("❌ Only R5/R6 can use this command.", ephemeral=True)
            return False
        return True

    @app_commands.command(name="create", description="Create a Frost event")
    @app_commands.describe(city="Frost city", date="YYYY-MM-DD", time="HH:MM")
    async def create(self, interaction: discord.Interaction, city: str, date: str, time: str):
        if not await self._leadership_only(interaction):
            return
        config = get_server(interaction.guild.id)
        config.setdefault("frost", []).append({"city": city, "date": date, "time": time})
        save_server()

        channel_id = config.get("frost_channel")
        channel = interaction.guild.get_channel(channel_id) if channel_id else None
        if channel:
            role = discord.utils.get(interaction.guild.roles, name="Frost")
            mention = role.mention if role else "@everyone"
            embed = discord.Embed(title="❄️ Frost Event", color=discord.Color.blue())
            embed.add_field(name="🏰 City", value=city, inline=True)
            embed.add_field(name="📅 Date", value=date, inline=True)
            embed.add_field(name="🕒 Time", value=time, inline=True)
            await channel.send(content=mention, embed=embed)

        await interaction.response.send_message("✅ Frost event created successfully.", ephemeral=True)

    @app_commands.command(name="list", description="List all Frost events")
    async def list(self, interaction: discord.Interaction):
        if not await self._leadership_only(interaction):
            return
        config = get_server(interaction.guild.id)
        frost = config.get("frost", [])
        if not frost:
            await interaction.response.send_message("❄️ No Frost events found.")
            return
        embed = discord.Embed(title="❄️ Frost Events", color=discord.Color.blue())
        for index, event in enumerate(frost, start=1):
            embed.add_field(name=f"{index}. {event['city']}", value=f"📅 {event['date']}\n🕒 {event['time']}", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="edit", description="Edit a Frost event")
    @app_commands.describe(number="Event number from /frost list", city="New city", date="YYYY-MM-DD", time="HH:MM")
    async def edit(self, interaction: discord.Interaction, number: int, city: str, date: str, time: str):
        if not await self._leadership_only(interaction):
            return
        config = get_server(interaction.guild.id)
        frost = config.get("frost", [])
        if number < 1 or number > len(frost):
            await interaction.response.send_message("❌ Invalid event number.", ephemeral=True)
            return
        frost[number - 1].update({"city": city, "date": date, "time": time})
        save_server()
        await interaction.response.send_message(
            f"✏️ Frost event #{number} updated!\n❄️ City: **{city}**\n📅 Date: **{date}**\n🕒 Time: **{time}**"
        )

    @app_commands.command(name="delete", description="Delete a Frost event")
    @app_commands.describe(number="Event number from /frost list")
    async def delete(self, interaction: discord.Interaction, number: int):
        if not await self._leadership_only(interaction):
            return
        config = get_server(interaction.guild.id)
        frost = config.get("frost", [])
        if number < 1 or number > len(frost):
            await interaction.response.send_message("❌ Invalid event number.", ephemeral=True)
            return
        removed = frost.pop(number - 1)
        save_server()
        await interaction.response.send_message(f"🗑️ Deleted Frost event **{removed['city']}** ({removed['date']} {removed['time']})")

    @app_commands.command(name="clear", description="Delete all Frost events")
    async def clear(self, interaction: discord.Interaction):
        if not await self._leadership_only(interaction):
            return
        config = get_server(interaction.guild.id)
        config["frost"] = []
        save_server()
        await interaction.response.send_message("🧹 All Frost events have been deleted.")

    @app_commands.command(name="addmap", description="Upload or replace the fitted Frozen Realm map")
    @app_commands.describe(image="Upload the complete fitted Frost map image")
    async def addmap(self, interaction: discord.Interaction, image: discord.Attachment):
        if not await self._leadership_only(interaction):
            return
        if not image.content_type or not image.content_type.startswith("image/"):
            await interaction.response.send_message("❌ Please upload an image file.", ephemeral=True)
            return

        config = get_server(interaction.guild.id)
        config["frost_map_url"] = image.url
        config["frost_map_name"] = image.filename
        save_server()

        await interaction.response.send_message(
            "✅ **Fitted Frost map saved.**\n"
            "Use `/frost map` to display it. R5/R6 can upload another image with `/frost addmap` anytime to replace it.",
            ephemeral=True,
        )

    @app_commands.command(name="map", description="Display the complete fitted Frozen Realm map")
    async def map(self, interaction: discord.Interaction):
        if not await self._leadership_only(interaction):
            return
        config = get_server(interaction.guild.id)
        url = config.get("frost_map_url")
        if not url:
            await interaction.response.send_message(
                "❄️ No fitted Frost map has been uploaded yet. R5/R6 can use `/frost addmap` to upload one.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(title="❄️ Frozen Realm — Complete Fitted Map", color=discord.Color.blue())
        embed.set_image(url=url)
        embed.set_footer(text="Shade • Frost Leadership Map")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="clearmap", description="Remove the saved fitted Frost map")
    async def clearmap(self, interaction: discord.Interaction):
        if not await self._leadership_only(interaction):
            return
        config = get_server(interaction.guild.id)
        config.pop("frost_map_url", None)
        config.pop("frost_map_name", None)
        save_server()
        await interaction.response.send_message("🧹 Saved fitted Frost map removed.", ephemeral=True)

    @app_commands.command(name="setrules", description="Set the Frost rules used by Shade")
    @app_commands.describe(rules="Paste the complete Frost rules")
    async def setrules(self, interaction: discord.Interaction, rules: str):
        if not await self._leadership_only(interaction):
            return
        if len(rules) > 4000:
            await interaction.response.send_message("❌ Rules are too long. Keep them under 4000 characters.", ephemeral=True)
            return
        config = get_server(interaction.guild.id)
        config["frost_rules"] = rules
        save_server()
        await interaction.response.send_message("✅ Frost rules saved. Leadership can use `/frost rules` anytime.", ephemeral=True)

    @app_commands.command(name="rules", description="Display the saved Frost rules")
    async def rules(self, interaction: discord.Interaction):
        if not await self._leadership_only(interaction):
            return
        config = get_server(interaction.guild.id)
        rules = config.get("frost_rules")
        if not rules:
            await interaction.response.send_message(
                "📜 No Frost rules have been configured yet. R5/R6 can use `/frost setrules` to save the alliance rules.",
                ephemeral=True,
            )
            return
        embed = discord.Embed(title="❄️ Frost Rules", description=rules, color=discord.Color.blue())
        embed.set_footer(text="Shade • Frost Leadership")
        await interaction.response.send_message(embed=embed)


def setup(bot):
    try:
        bot.tree.add_command(Frost())
    except Exception:
        pass
