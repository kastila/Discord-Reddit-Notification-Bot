import praw
import os
import time

def logIn():
    username = os.getenv('REDDIT_BOT_USERNAME')
    password = os.getenv('REDDIT_BOT_PASSWORD')
    client_id = os.getenv('REDDIT_BOT_ID')
    client_secret = os.getenv('REDDIT_BOT_SECRET')
    user_agent = os.getenv('REDDIT_BOT_AGENT')
    return  praw.Reddit(client_id=client_id, client_secret=client_secret, password=password, username=username, user_agent=user_agent)

def ScrapePosts(sub, keywords):
    reddit = logIn()
    posts = []
    try:
        subreddit = reddit.subreddit(sub)

        print("reddit script running")

        # checks for any new post
        for submission in subreddit.new(limit = 35):
            if(keywords == {'Everything*':None}):
                posts.append(submission)
            else:
                for keyword in keywords:
                    title = cleanTitle(submission.title)
                    if True in [word.startswith(keyword) for word in title.split()]:
                        posts.append(submission)
                        break
                    elif submission.link_flair_text:
                        flair = cleanTitle(submission.link_flair_text)
                        if keyword == flair:
                            posts.append(submission)
                            break
        time.sleep(2)            
    except Exception as error: 
        raise error
        time.sleep(5)
    return posts

def getSubredditName(sub):
    reddit = logIn()
    try: 
        subreddit = reddit.subreddit(sub)
        subreddit.id
        return subreddit.display_name
    except Exception:
        return None

def cleanWord(word):
    for c in '\"[]{}()*_,~':
        if c in word:
            word = word.replace(c,"")
    return word.lower().strip()

def cleanTitle(title):
    for c in "\"[]{}()*_,~":
        if c in title:
            title = title.replace(c," ")
    return title.lower().strip()