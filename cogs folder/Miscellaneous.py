import discord
import os
import asyncio
import random
import json
from discord.ext import commands

class Miscellaneous(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.command()
    async def ping(self,ctx):
        await ctx.send("pong")

    @commands.Cog.listener()
    async def on_guild_join(self,guild):
        with open('guilds.json','r') as file:
            guildsData = json.load(file)

        try:
            info = {
                "guildID":guild.id,
                "textChannel":guild.text_channels[0].id,
                "search":{}
                    }
            guildsData.append(info)

            channel = self.client.get_channel(guild.text_channels[0].id)
            await channel.send('Thanks for using Reddit Post Alert Bot\n'+
                                'Channel ' + str(guild.text_channels[0]) + ' is currently set to receive posts\n' +
                                'Use !changeChannelFeed to change channelFeed and !addSubreddit to add subreddits to search in')
        except IndexError:
            to_leave = self.client.get_guild(guild.id)
            await to_leave.leave()

        with open('guilds.json','w') as file:
            json.dump(guildsData,file,indent = 2)  
    
    @commands.Cog.listener()
    async def on_guild_remove(self,guild):
        with open('guilds.json','r') as file:
            guildsData = json.load(file)
        index = next((i for i,item in enumerate(guildsData) if item["guildID"] == int(guild.id)), None)

        del guildsData[index]

        with open('guilds.json','w') as file:
            json.dump(guildsData,file,indent = 2)  


def setup(client):
    client.add_cog(Miscellaneous(client))