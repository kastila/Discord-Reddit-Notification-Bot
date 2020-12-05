import discord
import os
import asyncio
from discord.ext import commands
from pymongo import MongoClient

MongoDBString = os.getenv('MONGODB_STRING')
botID = os.getenv('DISCORD_BOT_ID')
client = commands.Bot(command_prefix='!')

@client.event
async def on_ready():
    print('Bot ready')

    cluster = MongoClient(MongoDBString)
    db = cluster['discordbot']
    collections = db['guildsData']

    for guild in client.guilds:
        guildFound = collections.find_one({"guildID":guild.id})
        if not guildFound:
            info = {
                "guildID":guild.id,
                "search":{}
                    }
            collections.insert(info)

    cluster.close()

@client.event
async def on_guild_join(guild):
        cluster = MongoClient(MongoDBString)
        db = cluster['discordbot']
        collections = db['guildsData']

        try:
            channel = client.get_channel(guild.text_channels[0].id)

            info = {
            "guildID":guild.id,
            "search":{}
                }
            collections.insert(info)

            await channel.send('Thanks for using Reddit Post Alert Bot\n type !help for a list of commands')   
        except IndexError:
            to_leave = client.get_guild(guild.id)
            await to_leave.leave()
        
        cluster.close()

@client.event
async def on_guild_remove(guild):
    cluster = MongoClient(MongoDBString)
    db = cluster['discordbot']
    collections = db['guildsData']

    collections.delete_many({'guildID':guild.id})

    cluster.close()

for file in os.listdir('cogs'):
    if file.endswith('.py'):
        client.load_extension(f'cogs.{file[:-3]}')

client.run(botID)