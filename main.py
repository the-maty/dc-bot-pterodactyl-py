import discord
from discord.ext import commands, tasks
from config.config import token

bot = commands.Bot(command_prefix="?")

@bot.event
async def on_ready():
    print("Bot {} is up and running".format(bot.user.name))
    #print("ID: {}".format(bot.user.id))
    # Setting `Watching` status ALL TIME
    #await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="tvou rodinu"))

bot.load_extension('cogs.petro')
                                 
bot.run(token)