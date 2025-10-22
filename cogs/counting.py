import nextcord
from nextcord.ext import commands
from config import *

import nextcord
from nextcord.ext import commands
import json
from config import COUNTING_ID

SAVE_FILE = "count_data.json"

class Counting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.count = 0
        self.last_id = 0
        self.load_count()

    def load_count(self):
        try:
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
                self.count = data.get("count", 0)
                self.last_id = data.get("last_id", 0)
        except FileNotFoundError:
            self.count = 0
            self.last_id = 0

    def save_count(self):
        with open(SAVE_FILE, "w") as f:
            json.dump({"count": self.count, "last_id": self.last_id}, f)

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.author.bot:
            return
        if message.channel.id != COUNTING_ID:
            return

        if message.author.id == self.last_id:
            await message.reply("Nie możesz liczyć dwa razy pod rząd", delete_after=5)
            await message.delete(delay=5)
            return
        try:
            num = int(message.content)
        except ValueError:
            await message.reply("To nie liczba", delete_after=5)
            await message.delete(delay=5)
            return

        if num != self.count - 1:
            await message.reply("Zła liczba", delete_after=5)
            await message.delete(delay=5)
            return

        self.count = num
        self.last_id = message.author.id
        self.save_count()

def setup(bot):
    bot.add_cog(Counting(bot))
