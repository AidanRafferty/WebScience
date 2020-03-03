import time
import tweepy
from authenticate import authenticate
from pymongo import MongoClient
from save_tweet import save
from trends import get_current_trends

client = MongoClient()
mongo_client = MongoClient('localhost', 27017)

'''
Empty all the current collections in the database 
'''
database = mongo_client.Tweets
for collection in database.list_collection_names():
    print(collection)
    print(database[collection].drop())

# Collections for retweets, normal tweets and quote tweets
normal = database.Normal

# ensure that the same tweet cannot be stored more than once in any of the tables (collections)
database.Normal.create_index("id", unique=True, dropDups=True)


# override tweepy.StreamListener to add logic to on_status
class MyStreamListener(tweepy.StreamListener):
    counter = 0

    def on_status(self, status):

        # find the tweet type - tweet, retweet, quote

        # find the details

        # save to the correct table on MongoDB

        # if is a retweet
        if hasattr(status, 'retweeted_status'):

            # if is an extended retweet
            if status.retweeted_status.truncated:

                # save the retweet to the table for retweets and pass in the text which is from the extended tweet
                save(status, status.retweeted_status.extended_tweet['full_text'], True, False)

            else:

                # otherwise the retweeted tweet is not extended so pass in the normal text
                save(status, status.text, True, False)

        # if is a quoted status
        elif hasattr(status, 'quoted_status'):

            # initially the tweet and quote are not extended
            quote_text = status.text

            # if the quote is extended
            if status.truncated:
                # set the quote text as the extended text
                quote_text = status.extended_tweet['full_text']

            # save the quote to the mongoDB database
            save(status, quote_text, False, True)

        # otherwise, the status is a normal tweet from a user
        else:

            # if is an extended tweet
            if status.truncated:

                # the text to be saved is taken from the extended tweet
                save(status, status.extended_tweet['full_text'], False, False)

            # otherwise
            else:

                # the text to be saved is from the status
                save(status, status.text, False, False)

        '''
        3 kinds 
        --------
        tweet - usual object 

        retweet - shown by retweeted_status object existence in the status object
            the status text is that of the tweet that has been retweeted

        quote_tweet - shown by the existence of the quote_staus object in the status object
            These are basically retweets only with added comments by the retweeter
            the text is the retweet comment

        '''

    def on_error(self, status_code):
        # if you get 420 then timeout
        if status_code == 420:
            return False


api = authenticate()

while True:

    try:

        trends = get_current_trends()
        keywords = []

        for i in range(len(trends)):
            keywords.append(trends[0]['trends'][i]['name'])

        print(trends)

        myStreamListener = MyStreamListener()

        myStream = tweepy.Stream(auth = api.auth, listener=myStreamListener)

        myStream.filter(track=keywords,  languages=["en"])

    except Exception as e:
        print(str(e))
        time.sleep(5)
