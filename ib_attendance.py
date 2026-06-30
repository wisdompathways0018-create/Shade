import discord


class IBAttendanceView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)