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


    @commands.command(description='Adds a subReddit to search.',usage = '<Subreddit Name> <optional keywords>\n\'/[]{}()*-_ characters will be omitited from keywords')
    async def addSubreddit(self,ctx,subReddit,*keyWords):
        with open('guilds.json','r') as file:
            guilds = json.load(file)
        index = next((i for i,item in enumerate(guilds) if item["guildID"] == int(ctx.guild.id)), None)
        

        subName = RedditWebScraper.getSubredditName(subReddit)
        if subName:
            if not(subName in guilds[index]['search']):
                guilds[index]['search'][subName] = []
                for word in keyWords:
                    if not(word in guilds[index]['search'][subName]):
                        for c in "'/[]{}()*-_":
                            if c in word:
                                word = word.replace(c,"")
                        guilds[index]['search'][subName].append(word)
                await ctx.send("Now searching in these subreddits:" + str(guilds[index]["search"].keys())[10:-1])
            else:
                await ctx.send("Already searching in r/" + subReddit)
        else:
            await ctx.send("r/" + subReddit + " not found")

        with open('guilds.json','w') as file:
            json.dump(guilds,file,indent = 2)


    @commands.command(description='Removes a subReddit from the search', usage ='<Subreddit name>')
    async def removeSubreddit(self,ctx,subReddit):
        with open('guilds.json','r') as file:
            guilds = json.load(file)
        index = next((i for i,item in enumerate(guilds) if item["guildID"] == int(ctx.guild.id)), None)

        try:
            del guilds[index]['search'][subReddit]
            await ctx.send( "Removed r/" + "from search\n" 
                            "Now searching in these subreddits:" + str(guilds[index]["search"].keys())[10:-1])
        except KeyError:
            await ctx.send("Was not searching in r/" + subReddit)

        with open('guilds.json','w') as file:
            json.dump(guilds,file,indent = 2)

    @commands.command(description='Changes search critera to post all new posts from a subreddit' ,usage ='<Subreddit name>')
    async def searchAllNew(self,ctx,subReddit):
        with open('guilds.json','r') as file:
            guilds = json.load(file)
        index = next((i for i,item in enumerate(guilds) if item["guildID"] == int(ctx.guild.id)), None)

        subName = RedditWebScraper.getSubredditName(subReddit)
        if subName:
            if not(subName in guilds[index]['search']):
                guilds[index]['search'][subName] = {'Everything*':None}
                await ctx.send("Now searching in these subreddits:" + str(guilds[index]["search"].keys())[10:-1])
            elif guilds[index]['search'][subName] != {'everything*':None}:
                guilds[index]['search'][subName] = {'Everything*':None}
                await ctx.send("Now searching in these subreddits:" + str(guilds[index]["search"].keys())[10:-1])
            else:
                await ctx.send("Already searching all new posts in r/" + subReddit)
        else:
            await ctx.send("r/" + subReddit + " not found")

        with open('guilds.json','w') as file:
            json.dump(guilds,file,indent = 2)

    @commands.command(description='Adds keyterms to a subReddit\'s search critera' ,usage ='<Subreddit name> <keyterms to add>\n\'/[]{}()*-_ characters will be omitited from keywords')
    async def addKeywords(self,ctx,subReddit,*keyWords):
        with open('guilds.json','r') as file:
            guilds = json.load(file)
        index = next((i for i,item in enumerate(guilds) if item["guildID"] == int(ctx.guild.id)), None)

        if subReddit in guilds[index]['search']:
            if guilds[index]['search'][subReddit] == {'Everything*':None}:
                guilds[index]['search'][subReddit] = []
            for word in keyWords:
                if not(word in guilds[index]['search'][subReddit]):
                    for c in "'/[]{}()*-_":
                            if c in word:
                                word = word.replace(c,"")
                    guilds[index]['search'][subReddit].append(word)
            await ctx.send("Search keyWords updated: r/" + subReddit + " " + str(guilds[index]["search"][subReddit]))
        else:
            await ctx.send("Was not searching in r/" + subReddit )

        with open('guilds.json','w') as file:
            json.dump(guilds,file,indent = 2)

    @commands.command(description='Remove keyterms from a subReddit\'s search critera',usage ='<Subreddit name> <keyterms to remove>')
    async def removeKeywords(self,ctx,subReddit,*keyWords):
        with open('guilds.json','r') as file:
            guilds = json.load(file)
        index = next((i for i,item in enumerate(guilds) if item["guildID"] == int(ctx.guild.id)), None)

        if subReddit in guilds[index]['search']:
            if guilds[index]['search'][subReddit] != {'Everything*':None}:
                for word in keyWords:
                    if word in guilds[index]['search'][subReddit]:
                        guilds[index]['search'][subReddit].remove(word)
                await ctx.send("Search keyWords updated: r/" + subReddit + " " + str(guilds[index]["search"][subReddit]))
            else:
                await ctx.send("Currently searching in all new post in r/" + subReddit + " no keywords to remove")
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
            if guilds[index]['search'][subReddit] == {'Everything*':None}:
                msg += f"r/{str(subReddit)}: Searching all posts*\n"
            else:
                msg += f"r/{str(subReddit)}: {str(guilds[index]['search'][subReddit])}\n"

        if msg:
            await ctx.send(msg)
        else:
            await ctx.send("Currently not searching in any Subreddits. Try !addSubreddit to add one")

    @commands.command(description = 'Change channel to send found reddit posts', usage ='<name of channel>')
    async def changeChannelFeed(self,ctx,channelName):
        with open('guilds.json','r') as file:
            guilds = json.load(file)
        index = next((i for i,item in enumerate(guilds) if item["guildID"] == int(ctx.guild.id)), None)

        channel = discord.utils.get(ctx.guild.channels, name=channelName)
        if channel is not None:
            guilds[index]['textChannel'] = channel.id
            await ctx.send('Channel ' + str(channel.name) + ' is now set currently set to receive posts')
        else:
            await ctx.send('Channel ' + channelName + ' not Found')

        with open('guilds.json','w') as file:
            json.dump(guilds,file,indent = 2)

    @commands.Cog.listener()
    async def on_command_error(self,ctx, error):
        if isinstance(error, commands.InvalidEndOfQuotedStringError) or isinstance(error, commands.ExpectedClosingQuoteError):
            await ctx.send("Each \" must have an accompaning closing \"")
        else:
            raise error
    
async def findPosts(subReddits,keyWords,channel):
    try:
        history =  [ msg.content for msg in await channel.history(limit = 1000).flatten()]
        for i,sub in enumerate(subReddits):
            posts = RedditWebScraper.ScrapePosts(sub, keyWords[i])
            for p in posts:
                line = f"Title: {p.title} {p.url}"
                if line not in history:
                    await channel.send(line)
    except AttributeError:
        pass              
        

def setup(client):
    client.add_cog(GetRedditPost(client))