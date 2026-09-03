import discord
from discord import app_commands

from config import get_server, save_server
from permissions import is_leadership


# These are gameplay rules/notes based on the current Legion of Frostborne
# mechanics. Server/alliance-specific diplomacy rules should be added by R5/R6.
DEFAULT_FROST_RULES = [
    "❄️ Follow R5/R6 leadership instructions during Frost operations.",
    "🛡️ Protect alliance territory, cities, checkpoints, and Thermal Towers as assigned.",
    "⚔️ Do not attack friendly/federation players or structures. Follow all diplomatic agreements.",
    "🏰 Only attack cities/checkpoints when leadership has authorized the target and route.",
    "🗼 Keep Thermal Tower coverage and construction priorities aligned with the leadership plan.",
    "👁️ Use shared vision/proximity and report enemy movements or important targets to leadership.",
    "🚫 Do not start unauthorized rallies, city attacks, checkpoint attacks, or major PvP actions.",
    "📍 Follow assigned zones, rally points, garrison instructions, and relocation plans.",
    "🧊 Prepare troops, healing, relocations, shields, and speedups before scheduled operations.",
    "📢 Keep Frost communication clear; use the designated Frost channel for important calls.",
    "🤝 Help alliance members with defense, garrisons, rallies, construction, and assigned objectives.",
    "🏆 The final objective and strategy are determined by alliance leadership for the current round.",
]


class FrostGuide(app_commands.Group):
    def __init__(self):
        super().__init__(name="frost", description="Frost leadership map and rules")

    async def _leadership_only(self, interaction: discord.Interaction) -> bool:
        if interaction.guild is None:
            await interaction.response.send_message("❌ Server only.", ephemeral=True)
            return False
        if not is_leadership(interaction.user):
            await interaction.response.send_message("❌ Only R5/R6 can use this command.", ephemeral=True)
            return False
        return True

    @app_commands.command(name="map", description="Show the saved Frozen Realm map")
    async def map(self, interaction: discord.Interaction):
        if not await self._leadership_only(interaction):
            return

        config = get_server(interaction.guild.id)
        maps = config.get("frost_map_images", [])
        if not maps:
            await interaction.response.send_message(
                "❌ No Frost map images are configured yet. R5/R6 can use **/frost addmap** "
                "with each map screenshot once, then /frost map will display them.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message("❄️ **Frozen Realm — Complete Frost Map**")
        for index, url in enumerate(maps, start=1):
            embed = discord.Embed(title=f"❄️ Frozen Realm Map • Section {index}")
            embed.set_image(url=url)
            await interaction.channel.send(embed=embed)

    @app_commands.command(name="addmap", description="Save one Frost map screenshot for /frost map")
    @app_commands.describe(image="Upload one Frozen Realm map screenshot")
    async def addmap(self, interaction: discord.Interaction, image: discord.Attachment):
        if not await self._leadership_only(interaction):
            return

        if not image.content_type or not image.content_type.startswith("image/"):
            await interaction.response.send_message("❌ Please upload an image file.", ephemeral=True)
            return

        config = get_server(interaction.guild.id)
        maps = config.setdefault("frost_map_images", [])
        if image.url not in maps:
            maps.append(image.url)
            save_server()

        await interaction.response.send_message(
            f"✅ Frost map section saved (**{len(maps)}** total). Use /frost map when all sections are uploaded.",
            ephemeral=True,
        )

    @app_commands.command(name="clearmap", description="Remove all saved Frost map screenshots")
    async def clearmap(self, interaction: discord.Interaction):
        if not await self._leadership_only(interaction):
            return
        config = get_server(interaction.guild.id)
        config["frost_map_images"] = []
        save_server()
        await interaction.response.send_message("🗑️ Frost map images cleared.", ephemeral=True)

    @app_commands.command(name="rules", description="Show the Frost leadership rules")
    async def rules(self, interaction: discord.Interaction):
        if not await self._leadership_only(interaction):
            return

        config = get_server(interaction.guild.id)
        rules = config.get("frost_rules") or DEFAULT_FROST_RULES

        embed = discord.Embed(
            title="❄️ Legion of Frostborne • Leadership Rules",
            description="\n".join(f"**{i}.** {rule}" for i, rule in enumerate(rules, start=1)),
            color=discord.Color.blue(),
        )
        embed.set_footer(text="Shade • Frost Leadership")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="setrules", description="Replace the Frost rules with your alliance rules")
    @app_commands.describe(rules="Rules separated with | characters")
    async def setrules(self, interaction: discord.Interaction, rules: str):
        if not await self._leadership_only(interaction):
            return

        parsed = [rule.strip() for rule in rules.split("|") if rule.strip()]
        if not parsed:
            await interaction.response.send_message("❌ Add at least one rule.", ephemeral=True)
            return
        if len(parsed) > 20:
            await interaction.response.send_message("❌ Maximum 20 rules.", ephemeral=True)
            return

        config = get_server(interaction.guild.id)
        config["frost_rules"] = parsed
        save_server()
        await interaction.response.send_message(
            f"✅ Saved **{len(parsed)}** Frost rules. Use /frost rules to display them.",
            ephemeral=True,
        )


def setup(bot):
    try:
        bot.tree.add_command(FrostGuide())
    except Exception:
        pass
