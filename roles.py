import discord
from discord import app_commands


class RoleView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    async def toggle_role(
        self,
        interaction: discord.Interaction,
        role_name: str
    ):

        if interaction.guild is None:
            return

        role = discord.utils.get(
            interaction.guild.roles,
            name=role_name
        )

        if role is None:
            await interaction.response.send_message(
                f"❌ Role '{role_name}' not found.",
                ephemeral=True
            )
            return

        member = interaction.user

        if role in member.roles:

            await member.remove_roles(role)

            await interaction.response.send_message(
                f"➖ Removed **{role.name}**.",
                ephemeral=True
            )

        else:

            await member.add_roles(role)

            await interaction.response.send_message(
                f"✅ Added **{role.name}**.",
                ephemeral=True
            )

    @discord.ui.button(
        label="❄ Frost",
        style=discord.ButtonStyle.blurple
    )
    async def frost(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.toggle_role(interaction, "Frost")

    @discord.ui.button(
        label="🏰 IB",
        style=discord.ButtonStyle.green
    )
    async def ib(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.toggle_role(interaction, "IB")

    @discord.ui.button(
        label="🛡️ Alliance Supremacy",
        style=discord.ButtonStyle.secondary
    )
    async def supremacy(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.toggle_role(
            interaction,
            "Alliance Supremacy"
        )

    @discord.ui.button(
        label="⚔️ KE",
        style=discord.ButtonStyle.red
    )
    async def ke(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.toggle_role(interaction, "KE")


class RoleCommands(app_commands.Group):

    def __init__(self):
        super().__init__(
            name="roles",
            description="Notification roles"
        )

    @app_commands.command(
        name="panel",
        description="Send the notification role panel"
    )
    async def panel(
        self,
        interaction: discord.Interaction
    ):

        embed = discord.Embed(
            title="🔔 Notification Roles",
            description=(
                "Choose which notifications you want.\n\n"
                "Click a button to add or remove a role."
            ),
            color=discord.Color.dark_gray()
        )

        embed.add_field(
            name="Available Roles",
            value=(
                "❄ Frost\n"
                "🏰 IB\n"
                "🛡️ Alliance Supremacy\n"
                "⚔️ KE"
            ),
            inline=False
        )

        await interaction.response.send_message(
            embed=embed,
            view=RoleView()
        )


def setup(bot):
    print("Loading roles.py...")
    bot.add_view(RoleView())
    bot.tree.add_command(RoleCommands())
    print("Roles command registered!")