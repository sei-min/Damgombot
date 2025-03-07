import discord
from discord.ext import commands
from discord import app_commands

class DamgomConfigure:
    def __init__(self):
        # Configure intents
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        # Initialize the bot with intents
        self.app_commands = app_commands
        self.bot = commands.Bot(
            command_prefix='/',
            intents=self.intents,
            help_command=None
        )

