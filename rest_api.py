import time
import tweepy
from pymongo import MongoClient
from save_tweet import save
from authenticate import authenticate
from trends import get_current_trends

client = MongoClient()
mongo_client = MongoClient('localhost', 27017)
'''
The stream will be run before the rest and so no need to drop the tables here
'''
database = mongo_client.Tweets

# Collection for tweets
normal = database.Normal

'''
function that processes a collection of tweets returned from REST API calls
'''


def process_tweets(tweets):
    for tweet in tweets:
        if hasattr(tweet, "retweeted_status"):
            # print("The retweeter", tweet.user.screen_name)
            # print("The tweeter", tweet.retweeted_status.user.screen_name)
            # print(tweet.retweeted_status.full_text)

            save(tweet, tweet.retweeted_status.full_text, True, False)

        elif hasattr(tweet, 'quoted_status'):

            save(tweet, tweet.full_text, False, True)

        else:

            save(tweet, tweet.full_text, False, False)


api = authenticate()

# users of interest in UK
users_of_interest = ["ScotlandSky", "ClydeSSB", "BBCSport", "BBCSportScot", "BBCNews", "SkyNews",
                     "SkySportsNews", "chris_sutton73", "btsportfootball", "MailSport", "sportbible",
                     "guardian", "SkyNewsBreak", "Record_Sport", "TheSportsman", "STVNews", "ScotRail",
                     "PaddyPower", "bbc5live", "BBCPolitics", "itvnews", "Channel4News", "TrustyTransfers",
                     "Daily_Record", "goal"]

# have the stream call here and have async set to true so that the rest calls are made while its streaming
# possibly have a script that runs the REST API and then one that runs the stream or keep it how it is
print("users of interest")
for user in users_of_interest:
    searchTweets = [status for status in tweepy.Cursor(api.user_timeline, screen_name=user, lang='en',
                                                       tweet_mode='extended', count=200).items(2000)]
    print(user)
    print(len(searchTweets))
    process_tweets(searchTweets)

# get the current trends here every 15 minutes within a while true that sleeps for 900 seconds or so every call so that
# the restrictions are not broken
# print("topics of interest")
# topics_of_interest = ["celtic", "europa league", "Lennon", "Griff", "coronavid19"]
# for topic in topics_of_interest:
#     searchTweets = [status for status in tweepy.Cursor(api.search, q=topic, lang='en',
#                                                        tweet_mode='extended', count=200).items(1000)]
#     # print(len(searchTweets))
#     # print(searchTweets[0].full_text)
#     process_tweets(searchTweets)
#
# print("Getting trending tweets")
# function which gets the current Glasgow trends every 15 minutes and returns the last 1000 tweets for each


# get the last 200 tweets from the top trending topics every 15 minutes
while True:
    trends = get_current_trends()
    print("trends")
    for i in range(len(trends[0]['trends'])):
        try:
            print("trend = ", str(trends[0]['trends'][i]['name']))
            trendingTweets = api.search(q=trends[0]['trends'][i]['name'], lang='en', tweet_mode='extended',
                                        result_type='recent', count=200)
            process_tweets(trendingTweets)
        except:
            time.sleep(60)
            print("Error in trends received")

    print("sleeping for 15 minutes and will get the current trends then")
    time.sleep(900)


