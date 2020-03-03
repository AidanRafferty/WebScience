from pymongo import MongoClient

client = MongoClient()
mongo_client = MongoClient('localhost', 27017)
'''
Empty all the current collections in the database 
'''
database = mongo_client.Tweets

# Collections for retweets, normal tweets and quote tweets
normal = database.Normal


def save(tweet, text, is_retweet, is_quote):
    # if is retweet/quote then the username will be that of the retweeter/quoter
    tweet_id = tweet.id_str
    username = tweet.user.screen_name
    hashtags = tweet.entities['hashtags']
    user_mentions = tweet.entities['user_mentions']
    if is_retweet:
        retweeted_user = tweet.retweeted_status.user.screen_name
    else:
        retweeted_user = ""
    if is_quote:
        quoted_user = tweet.quoted_status.user.screen_name
    else:
        quoted_user = ""
    created = tweet.created_at
    entry = {'id': tweet_id, 'user': username, 'text': text, 'hashtags': hashtags, 'user_mentions': user_mentions,
             "is_rt": is_retweet, "retweeted_user": retweeted_user, "is_quote": is_quote, "quoted_user": quoted_user,
             'created': created, }
    # attempt to insert the tweet
    try:
        normal.insert_one(entry)
    except Exception as e:
        # This will be entered if the tweet is a duplicate
        print("Error saving tweet")
        print(e)
