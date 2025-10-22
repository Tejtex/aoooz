
import nextcord
from nextcord.ext import commands
from config import * 

intents = nextcord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="?", intents=intents)


initial_extensions = ['cogs.counting', 'cogs.runner']

for extension in initial_extensions:
    bot.load_extension(extension)

bot.run(TOKEN)
