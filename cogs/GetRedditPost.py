import os
import discord
from discord.ext import commands,tasks
from pymongo import MongoClient
import RedditWebScraper

MongoDBString = os.getenv('MONGODB_STRING')

class GetRedditPost(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.cluster = MongoClient(MongoDBString)
        self.collections = self.cluster['discordbot']['guildsData']

    def cleanWord(word):
        for c in '\"[]{}()*_,~':
            if c in word:
                word = word.replace(c,"")
        return word.lower()

    @tasks.loop(minutes = 20.0)
    async def searchPosts(self):
        for guild in self.client.guilds:
            guildInfo = self.collections.find_one({'guildID':guild.id})
            postIdsToAdd = []
            for sub in guildInfo['search'].items():
                channel = self.client.get_channel(sub[1]['textChannel'])
                if channel:
                    postIdsToAdd += await findPosts(sub[0],sub[1]['keyWords'],channel,guildInfo['postIDs'])
            self.collections.update_one({'guildID':guild.id},{'$push':{'postIDs':{'$each':postIdsToAdd,'$slice':-1000}}})

    @commands.command(description='Adds a subReddit to search.',usage = '<Subreddit Name> <Text channel name to send posts> Optional*<keywords(includes flairs and emojis)>\ncharacters \"[]{}()*_,~ will be omitited from keywords')
    async def addSubreddit(self,ctx,subReddit:str,textChannelName:str,*keyWords:cleanWord):
        guild = self.collections.find_one({"guildID":ctx.guild.id}) 
        subName = RedditWebScraper.getSubredditName(subReddit)
        channel = discord.utils.get(ctx.guild.channels, name=textChannelName)

        if subName and channel:
            if subName not in guild['search']:
                guild['search'][subName] = {'textChannel':channel.id, 'keyWords':[]}
                for word in keyWords:
                    if word not in guild['search'][subName]['keyWords'] and word:
                        guild['search'][subName]['keyWords'].append(word)
                self.collections.update_one({'guildID':guild['guildID']}, {'$set':{'search':guild['search']}})
                await ctx.send(f"Now searching in r/{subName} with search terms *{str(guild['search'][subName]['keyWords']).strip('[]')}* and sending to text channel *{textChannelName}*")
            else:
                await ctx.send(f"Already searching in r/{subName}")
        elif subName is None:
            await ctx.send(f"r/{subReddit} not found")
        elif channel is None:
            await ctx.send(f"Text channel *{textChannelName}* not found")
       
    @commands.command(description="Removes a subReddit from the search", usage ="<Subreddit name>")
    async def removeSubreddit(self,ctx,subReddit:str):
        guild = self.collections.find_one({"guildID":ctx.guild.id})
        subName = RedditWebScraper.getSubredditName(subReddit)

        try:
            del guild['search'][subName]
            self.collections.update_one({'guildID':guild['guildID']}, {'$set':{'search':guild['search']}})
            await ctx.send( f"Removed r/{subName} from search \nNow searching in these subreddits: {str(guild['search'].keys())[11:-2]}")
        except KeyError:
            await ctx.send("Was not searching in r/{subReddit}")

    @commands.command(description='Changes search critera to post all new posts from a subreddit' ,usage ='<Subreddit name>')
    async def searchAllNew(self,ctx,subReddit:str):
        guild = self.collections.find_one({"guildID":ctx.guild.id})
        subName = RedditWebScraper.getSubredditName(subReddit)

        if subName in guild['search']:
            if guild['search'][subName]['keyWords'] != {'Everything*':None}:
                guild['search'][subName]['keyWords'] = {'Everything*':None}
                self.collections.update_one({'guildID':guild['guildID']}, {'$set':{'search':guild['search']}})
                await ctx.send(f"Now set to search all new post from r/{subName}")
            else:
                await ctx.send(f"Already searching all new posts in r/{subName}")
        else:
            await ctx.send(f"Currenly not searching in r/{subReddit}\n Use *!addSubreddit* to add it before using this command")


    @commands.command(description='Adds keyterms to a subReddit\'s search critera' ,usage ='<Subreddit name> <keyterms to add(includes flairs and emojis)>\ncharacters \"[]{}()*_,~ will be omitited from keywords')
    async def addKeywords(self,ctx,subReddit:str,*keyWords:cleanWord):
        guild = self.collections.find_one({"guildID":ctx.guild.id})
        subName = RedditWebScraper.getSubredditName(subReddit)

        if subName in guild['search'] and keyWords:
            if guild['search'][subName]['keyWords'] == {'Everything*':None}:
                guild['search'][subName]['keyWords'] = []
            for word in keyWords:
                if word not in guild['search'][subName]['keyWords'] and word:
                    guild['search'][subName]['keyWords'].append(word)
            self.collections.update_one({'guildID':guild['guildID']}, {'$set':{'search':guild['search']}})
            await ctx.send(f"Search keyWords updated for r/{subName}: {str(guild['search'][subName]['keyWords']).strip('[]')}")
        elif not keyWords:
            await ctx.send(f"No keywords given")
        else:
            await ctx.send(f"Currently not searching in r/{subReddit}")

    @commands.command(description='Remove keyterms from a subReddit\'s search critera',usage ='<Subreddit name(case sensitive)> <keyterms to remove>')
    async def removeKeywords(self,ctx,subReddit:str,*keyWords:str):
        guild = self.collections.find_one({"guildID":ctx.guild.id})
        subName = RedditWebScraper.getSubredditName(subReddit)

        if subName in guild['search'] and keyWords:
            if guild['search'][subName]['keyWords'] != {'Everything*':None}:
                for word in keyWords:
                    if word.lower() in guild['search'][subName]['keyWords']:
                        guild['search'][subName]['keyWords'].remove(word.lower())
                self.collections.update_one({'guildID':guild['guildID']}, {'$set':{'search':guild['search']}})
                await ctx.send(f"Search keyWords updated for r/{subName}: {str(guild['search'][subName]['keyWords']).strip('[]')}")
            else:
                await ctx.send(f"Currently searching in all new post in r/{subName}. No keywords to remove")
        elif not keyWords:
            await ctx.send(f"No keywords given")
        else:
            await ctx.send(f"Currently not searching in r/{subReddit}")

    @commands.command(description = 'Lists subreddits being searched in and thier respective search keyterms')
    async def listSearch(self,ctx):
        guild = self.collections.find_one({"guildID":ctx.guild.id})

        msg = "```"
        for subReddit in guild['search']:
            try:
                channelName = self.client.get_channel(guild['search'][subReddit]['textChannel']).name
            except AttributeError:
                channelName = "None* Please update with new text channel or remove them from search"

            if guild['search'][subReddit]['keyWords'] == {'Everything*':None}:
                msgAdd = f"r/{str(subReddit)}: Searching all posts* | Text channel: {channelName}\n"
            elif not guild['search'][subReddit]['keyWords']:
                msgAdd = f"r/{str(subReddit)}: No keywords given | Text channel: {channelName}\n"
            else:
                msgAdd = f"r/{str(subReddit)}: {str(guild['search'][subReddit]['keyWords'])} | Text channel: {channelName}\n"

            if(len(msg + msgAdd) > 1994):
                await ctx.send(msg + '```')
                msg = '```' + msgAdd
            else:
                msg += msgAdd

        if msg:
            await ctx.send(msg + '```')
        else:
            await ctx.send("Currently not searching in any Subreddits. Try *!addSubreddit* to add one")

    @commands.command(description = 'Change channel to send found reddit posts', usage ='<name of channel>')
    async def changeChannelFeed(self,ctx,subReddit:str,textChannelName:str):
        guild = self.collections.find_one({"guildID":ctx.guild.id})
        subName = RedditWebScraper.getSubredditName(subReddit)
        channel = discord.utils.get(ctx.guild.channels, name=textChannelName)

        if channel and subName:
            guild['search'][subName]['textChannel'] = channel.id
            self.collections.update_one({'guildID':guild['guildID']}, {'$set':{'search':guild['search']}})
            await ctx.send(f"Text channel *{str(channel.name)}* is now set currently set to receive posts")
        elif not subName:
            await ctx.send(f"Currently not searching in r/{subReddit}")
        else:
            await ctx.send(f"Text channel *{textchannelName}* not Found")

    @commands.Cog.listener()
    async def on_command_error(self,ctx, error):
        if isinstance(error, commands.InvalidEndOfQuotedStringError) or isinstance(error, commands.ExpectedClosingQuoteError):
            await ctx.send("Each \" must have an accompaning closing \"")
        elif isinstance(error,commands.errors.MissingRequiredArgument):
            await ctx.send("Arguements Missing")
        else:
            raise error
    
async def findPosts(subReddit,keyWords,channel, postIds):
    posts = RedditWebScraper.ScrapePosts(subReddit, keyWords)
    addedPostIDs = []
    for p in posts:
        line = f"**r/{subReddit}**: {p.title}\n{p.url}"
        if p.id not in postIds:
            await channel.send(line)
            addedPostIDs.append(p.id)

    return addedPostIDs

def setup(client):
    client.add_cog(GetRedditPost(client))
