import praw
import re
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
        for submission in subreddit.new():
                for keyword in keywords:
                    if 0 in[word.find(keyword) for word in submission.title.lower().split()]:
                        print("found: " + submission.title )
                        posts.append(submission)
                        break
        time.sleep(1)            
    except Exception: 
        time.sleep(5)
    return posts

def sub_exists(sub):
    reddit = logIn()
    try: 
        results = reddit.subreddits.search_by_name(sub,include_nsfw=True, exact=True)
        if len(results) > 0:
            return True
        else:
            return False
    except Exception:
        return False