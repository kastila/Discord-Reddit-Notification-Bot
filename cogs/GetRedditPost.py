import discord
import os
import asyncio
from discord.ext import commands
from pymongo import MongoClient
import RedditWebScraper

MongoDBString = os.getenv('MONGODB_STRING')
class GetRedditPost(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        
        while True:
            cluster = MongoClient(MongoDBString)
            db = cluster['discordbot']
            collections = db['guildsData']

            for guild in self.client.guilds:
                guildInfo = collections.find_one({"guildID":guild.id})
                for sub in guildInfo['search'].items():
                    channel = self.client.get_channel(sub[1]['textChannel'])
                    if channel:
                        await findPosts(sub[0],sub[1]['keyWords'],channel)

            cluster.close()
            await asyncio.sleep(900)


    @commands.command(description='Adds a subReddit to search.',usage = '<Subreddit Name> <Text channel name to send posts> Optional*<keywords(includes flairs and emojis)>\ncharacters \"[]{}()*_,~ will be omitited from keywords')
    async def addSubreddit(self,ctx,subReddit:str,textChannelName:str,*keyWords:str):
        guild = getGuildFromMongoDB(ctx.guild.id) 
        subName = RedditWebScraper.getSubredditName(subReddit)
        channel = discord.utils.get(ctx.guild.channels, name=textChannelName)

        if subName and channel:
            if not(subName in guild['search']):
                guild['search'][subName] = {'textChannel':channel.id, 'keyWords':[]}
                for word in keyWords:
                    if not(word in guild['search'][subName]['keyWords']):
                        word = RedditWebScraper.cleanWord(word)
                        if word:
                            guild['search'][subName]['keyWords'].append(word)
                saveInMongoDB(guild)
                await ctx.send(f"Now searching in r/{subName} with search terms {guild['search'][subName]['keyWords']} and sending to text channel [{textChannelName}]")
            else:
                await ctx.send(f"Already searching in r/{subName}")
        elif subName is None:
            await ctx.send(f"r/{subReddit} not found")
        elif channel is None:
            await ctx.send(f"Text channel [{textChannelName}] not found")
       


    @commands.command(description="Removes a subReddit from the search", usage ="<Subreddit name>")
    async def removeSubreddit(self,ctx,subReddit:str):
        guild = getGuildFromMongoDB(ctx.guild.id)
        subName = RedditWebScraper.getSubredditName(subReddit)

        try:
            del guild['search'][subName]
            saveInMongoDB(guild)
            await ctx.send( f"Removed r/{subName}from search \nNow searching in these subreddits: {str(guild['search'].keys())[10:-1]}")
        except KeyError:
            await ctx.send("Was not searching in r/{subReddit}")


    @commands.command(description='Changes search critera to post all new posts from a subreddit' ,usage ='<Subreddit name>')
    async def searchAllNew(self,ctx,subReddit:str):
        guild = getGuildFromMongoDB(ctx.guild.id)
        subName = RedditWebScraper.getSubredditName(subReddit)

        if subName in guild['search']:
            if guild['search'][subName]['keyWords'] != {'Everything*':None}:
                guild['search'][subName]['keyWords'] = {'Everything*':None}
                saveInMongoDB(guild)
                await ctx.send(f"Now set to search all new post from r/{subName}")
            else:
                await ctx.send(f"Already searching all new posts in r/{subName}")
        else:
            await ctx.send(f"Currenly not searching in r/{subReddit}\n Use !addSubreddit to add it before using this command")


    @commands.command(description='Adds keyterms to a subReddit\'s search critera' ,usage ='<Subreddit name> <keyterms to add(includes flairs and emojis)>\ncharacters \"[]{}()*_,~ will be omitited from keywords')
    async def addKeywords(self,ctx,subReddit:str,*keyWords:str):
        guild = getGuildFromMongoDB(ctx.guild.id)
        subName = RedditWebScraper.getSubredditName(subReddit)

        if subName in guild['search'] and keyWords:
            if guild['search'][subName]['keyWords'] == {'Everything*':None}:
                guild['search'][subName]['keyWords'] = []
            for word in keyWords:
                if not(word in guild['search'][subName]['keyWords']):
                    word = RedditWebScraper.cleanWord(word)
                    if word:
                        guild['search'][subName]['keyWords'].append(word)
            saveInMongoDB(guild)
            await ctx.send(f"Search keyWords updated: r/{subName}: {str(guild['search'][subName]['keyWords'])}")
        elif not keyWords:
            await ctx.send(f"No keywords given")
        else:
            await ctx.send(f"Currently not searching in r/{subReddit}")

    @commands.command(description='Remove keyterms from a subReddit\'s search critera',usage ='<Subreddit name(case sensitive)> <keyterms to remove>')
    async def removeKeywords(self,ctx,subReddit:str,*keyWords:str):
        guild = getGuildFromMongoDB(ctx.guild.id)
        subName = RedditWebScraper.getSubredditName(subReddit)

        if subName in guild['search'] and keyWords:
            if guild['search'][subName]['keyWords'] != {'Everything*':None}:
                for word in keyWords:
                    if word.lower() in guild['search'][subName]['keyWords']:
                        guild['search'][subName]['keyWords'].remove(word.lower())
                saveInMongoDB(guild)
                await ctx.send(f"Search keyWords updated for r/{subName}: {guild['search'][subName]['keyWords']}")
            else:
                await ctx.send(f"Currently searching in all new post in r/{subName}. No keywords to remove")
        elif not keyWords:
            await ctx.send(f"No keywords given")
        else:
            await ctx.send(f"Currently not searching in r/{subReddit}")

    @commands.command(description = 'Lists subreddits being searched in and thier respective search keyterms')
    async def listInfo(self,ctx):
        guild = getGuildFromMongoDB(ctx.guild.id)

        msg = ""
        for subReddit in guild['search']:
            channelName = self.client.get_channel(guild['search'][subReddit]['textChannel']).name
            if guild['search'][subReddit]['keyWords'] == {'Everything*':None}:
                msgAdd = f"r/{str(subReddit)}: Searching all posts* | Text channel: {channelName}\n"
            elif not guild['search'][subReddit]['keyWords']:
                msgAdd = f"r/{str(subReddit)}: No keywords given | Text channel: {channelName}\n"
            else:
                msgAdd = f"r/{str(subReddit)}: {str(guild['search'][subReddit]['keyWords'])} | Text channel: {channelName}\n"

            if(len(msg) > 2000):
                await ctx.send(msg)
                msg = msgAdd
            else:
                msg += msgAdd

        if msg:
            await ctx.send(msg)
        else:
            await ctx.send("Currently not searching in any Subreddits. Try !addSubreddit to add one")

    @commands.command(description = 'Change channel to send found reddit posts', usage ='<name of channel>')
    async def changeChannelFeed(self,ctx,subReddit:str,textChannelName:str):
        guild = getGuildFromMongoDB(ctx.guild.id)
        subName = RedditWebScraper.getSubredditName(subReddit)
        channel = discord.utils.get(ctx.guild.channels, name=textChannelName)

        if channel and subName:
            guild['search'][subName]['textChannel'] = channel.id
            saveInMongoDB(guild)
            await ctx.send(f"Channel {str(channel.name)} is now set currently set to receive posts")
        elif not subName:
            await ctx.send(f"Currently not searching in r/{subReddit}")
        else:
            await ctx.send(f"Text channel [{channelName}] not Found")

    @commands.Cog.listener()
    async def on_command_error(self,ctx, error):
        if isinstance(error, commands.InvalidEndOfQuotedStringError) or isinstance(error, commands.ExpectedClosingQuoteError):
            await ctx.send("Each \" must have an accompaning closing \"")
        elif isinstance(error,commands.errors.MissingRequiredArgument):
            await ctx.send("Arguements Missing")
        else:
            raise error
    
async def findPosts(subReddit,keyWords,channel):
    history =  [ msg.content for msg in await channel.history(limit = 1000).flatten()]
    posts = RedditWebScraper.ScrapePosts(subReddit, keyWords)
    for p in posts:
        line = f"r/{subReddit}: {p.title} {p.url}"
        if line not in history:
            await channel.send(line)
              
        
def getGuildFromMongoDB(guildID):
    cluster = MongoClient(MongoDBString)
    db = cluster['discordbot']
    collections = db['guildsData']
    guildFound = collections.find_one({"guildID":guildID})
    cluster.close()
    return guildFound

def saveInMongoDB(guild):
    cluster = MongoClient(MongoDBString)
    db = cluster['discordbot']
    collections = db['guildsData']
    collections.update_one({'guildID':guild['guildID']}, {'$set':{'search':guild['search']}})
    cluster.close()

def setup(client):
    client.add_cog(GetRedditPost(client))