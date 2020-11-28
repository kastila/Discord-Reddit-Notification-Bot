import discord
import os
import asyncio
import json
from discord.ext import commands

botID = os.getenv('DISCORD_BOT_ID')

client = commands.Bot(command_prefix='!')

@client.event
async def on_ready():
    with open('guilds.json','r') as file:
        guildsData = json.load(file)

    for i, guild in enumerate(client.guilds):
        guildSaved = next((item for item in guildsData if item["guildID"] == guild.id), False)
        if not guildSaved:
            info = {
                "guildID":guild.id,
                "textChannel":guild.text_channels[0].id,
                "search":{}
                    }
            guildsData.append(info)
        elif len(guildsData) == len(client.guilds):
            textChannelSaved = next((item for item in guild.text_channels if guildsData[i]['textChannel'] == item.id), False)
            if not textChannelSaved:
                guildsData[i]['textChannel'] = guild.text_channels[0].id                

    with open('guilds.json','w') as file:
        json.dump(guildsData,file,indent = 2)  

for file in os.listdir("cogs folder"):
    if file.endswith('.py'):
        client.load_extension(f'cogs folder.{file[:-3]}')


client.run(botID)