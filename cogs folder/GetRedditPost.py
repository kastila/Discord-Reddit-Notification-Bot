import discord
import os
import asyncio
import json
from discord.ext import commands
import RedditWebScraper

class GetRedditPost(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print('Bot ready')

        while True:
            with open('guilds.json','r') as file:
                guilds = json.load(file)

            for guild in guilds:
                channel = self.client.get_channel(guild['textChannel'])
                await findPosts(guild['search'],list(guild['search'].values()),channel)

            await asyncio.sleep(900)


    @commands.command(description='Adds a subReddit to search.\nInputs: Subreddit name and then keyterms to search for.')
    async def addSubreddit(self,ctx,subReddit, *keyWords):
        with open('guilds.json','r') as file:
            guilds = json.load(file)
        index = next((i for i,item in enumerate(guilds) if item["guildID"] == int(ctx.guild.id)), None)

        if RedditWebScraper.sub_exists(subReddit):
            if not(subReddit in guilds[index]['search']):
                guilds[index]['search'][subReddit] = []
                for word in keyWords:
                    if not(word in guilds[index]['search'][subReddit]):
                        guilds[index]['search'][subReddit].append(word)
                await ctx.send("Now searching in these subreddits:" + str(guilds[index]["search"].keys())[10:-1])
            else:
                await ctx.send("Already searching in r/" + subReddit)
        else:
            await ctx.send("r/" + subReddit + " not found")

        with open('guilds.json','w') as file:
            json.dump(guilds,file,indent = 2)


    @commands.command(description='Removes a subReddit from the search.\nInputs: Subreddit name.')
    async def removeSubreddit(self,ctx,subReddit):
        with open('guilds.json','r') as file:
            guilds = json.load(file)
        index = next((i for i,item in enumerate(guilds) if item["guildID"] == int(ctx.guild.id)), None)

        try:
            del guilds[index]['search'][subReddit]
            await ctx.send( "Removed r/" + "from search\n" 
                            "Now searching in these subreddits:" + str(guilds[index]["search"].keys())[10:-1])
        except KeyError:
            await ctx.send("Was not searching in r/" + subReddit.content)

        with open('guilds.json','w') as file:
            json.dump(guilds,file,indent = 2)


    @commands.command(description='Adds keyterms to a subReddit\'s search critera.\nInputs: Subreddit name then the keyterms to add.')
    async def addKeywords(self,ctx,subReddit,*keyWords):
        with open('guilds.json','r') as file:
            guilds = json.load(file)
        index = next((i for i,item in enumerate(guilds) if item["guildID"] == int(ctx.guild.id)), None)

        if subReddit in guilds[index]['search']:
            for word in keyWords:
                if not(word in guilds[index]['search'][subReddit]):
                    guilds[index]['search'][subReddit].append(word)
            await ctx.send("Search keyWords updated: r/" + subReddit + " " + str(guilds[index]["search"][subReddit]))
        else:
            await ctx.send("Was not searching in r/" + subReddit )

        with open('guilds.json','w') as file:
            json.dump(guilds,file,indent = 2)

    @commands.command(description='Remove keyterms from a subReddit\'s search critera.\nInputs: Subreddit name then the keyterms to remove.')
    async def removeKeywords(self,ctx,subReddit,*keyWords):
        with open('guilds.json','r') as file:
            guilds = json.load(file)
        index = next((i for i,item in enumerate(guilds) if item["guildID"] == int(ctx.guild.id)), None)

        if subReddit in guilds[index]['search']:
            for word in keyWords:
                if word in guilds[index]['search'][subReddit]:
                    guilds[index]['search'][subReddit].remove(word)
            await ctx.send("Search keyWords updated: r/" + subReddit + " " + str(guilds[index]["search"][subReddit]))
        else:
            await ctx.send("Was not searching in r/" + subReddit )

        with open('guilds.json','w') as file:
            json.dump(guilds,file,indent = 2)

    @commands.command(description = 'Lists subreddits being searched in and thier respective search keyterms')
    async def listSearch(self,ctx):
        with open('guilds.json','r') as file:
            guilds = json.load(file)
        index = next((i for i,item in enumerate(guilds) if item["guildID"] == int(ctx.guild.id)), None)

        msg = ""
        for subReddit in guilds[index]['search']:
            msg += "r/" + str(subReddit) + ": " + str(guilds[index]['search'][subReddit]) + '\n'
        await ctx.send(msg)

    @commands.command(description = 'Change channel to send found reddit posts\nInput: name of channel')
    async def changeChannelFeed(self,ctx,channelName):
        with open('guilds.json','r') as file:
            guilds = json.load(file)
        index = next((i for i,item in enumerate(guilds) if item["guildID"] == int(ctx.guild.id)), None)

        channel = discord.utils.get(ctx.guild.channels, name=channelName)
        if channel is not None:
            guilds[index]['textChannel'] = channel.id
            await ctx.send('Channel ' + str(channel.name) + ' is now set currently set to receive posts')

        with open('guilds.json','w') as file:
            json.dump(guilds,file,indent = 2)

async def findPosts(subReddits,keyWords,channel):
    history =  [ msg.content for msg in await channel.history(limit = 100).flatten()]
    for i,sub in enumerate(subReddits):
        posts = RedditWebScraper.ScrapePosts(sub, keyWords[i])
        for p in posts:
            if p.url not in history:
                await channel.send(p.url)             
        

def setup(client):
    client.add_cog(GetRedditPost(client))