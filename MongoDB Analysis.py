from more_itertools import take
from pymongo import MongoClient
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import *
import re
import csv

client = MongoClient()
mongo_client = MongoClient('localhost', 27017)
# connects to the mongoDB database and empties it so that only the data from the current API calls are held

# do the same for hashtags possibly
database = mongo_client.Tweets

for collection in database.list_collection_names():
    print(collection)
    print("Total Tweets = " + str(database[collection].count_documents(filter={})))
    print("Retweets = " + str(database[collection].count_documents(filter={'is_rt': True})))
    print("Quotes = " + str(database[collection].count_documents(filter={'is_quote': True})))
    print("Normal Tweets  = " + str(database[collection].count_documents(filter={'is_quote': False, 'is_rt': False})))

all_tweets = list(database["Normal"].find(no_cursor_timeout=True))
retweets = list(database["Normal"].find(filter={"is_rt": True}, no_cursor_timeout=True))
quotes = list(database["Normal"].find(filter={"is_quote": True}, no_cursor_timeout=True))
normal_tweets = list(database["Normal"].find(filter={'is_quote': False, 'is_rt': False}, no_cursor_timeout=True))
'''
Write to CSV file the id of each tweet and the text
'''


def get_clean_tweet_text(all_tweets):
    texts = []
    for t in all_tweets:
        text = t['text']
        text = re.sub(r'@\S+|https?://\S+', '', text)
        texts.append(text)
    return texts


texts = get_clean_tweet_text(all_tweets)

tfidf_vectorizer = TfidfVectorizer(stop_words='english')
X = tfidf_vectorizer.fit_transform(texts)

clusters = 10
model = KMeans(n_clusters=clusters, init='k-means++', max_iter=200, n_init=1)
model.fit(X)

cluster_dict = {}

# calculate the number of tweets in each cluster
for label in model.labels_:
    if label not in cluster_dict.keys():
        cluster_dict[label] = 1
    else:
        cluster_dict[label] += 1

# print the number of tweets in each cluster
for i in range(clusters):
    print("Cluster = ", i, cluster_dict[i])

order_centroids = model.cluster_centers_.argsort()[:, ::-1]
terms = tfidf_vectorizer.get_feature_names()
print("top 10 terms in each cluster")
for i in range(clusters):
    print("Cluster " + str(i))
    print()
    for ind in order_centroids[i, :10]:
        print(terms[ind])
    print()
    print()

'''
Have a function which given a cluster number returns all the tweets from this cluster 
This collection of tweets can then be fed into the functions for getting the most important 
(mentioned) users and the interaction graphs
'''


def get_tweets_from_cluster(cluster_labels, cluster_number, tweets):
    cluster_tweets = []
    # for each cluster number in the model
    for i in range(len(tweets)):
        # if the cluster number at this index is the cluster_number being searched for
        if cluster_labels[i] == cluster_number:
            # add this tweet from all_tweets to the list of tweets at this cluster
            cluster_tweets.append(tweets[i])
    # return the tweets from this cluster
    return cluster_tweets

    # to get the triads go through the user interactions and get the 3 linked ties between the author of the tweet, the
    # user mentioned and each user that the mentioned user has connected with


'''
Can have a dictionary where the keys are usernames and each value is a list of tuples holding the other users it is connected to and the freq
Then have another with all the number of users this is connected to

put the tweets into a csv

the importa nce of a user - how many times they are mentioned
'''


# get the top mentioned users from the list of mongoDB documents provided
def get_top_mentioned_users(tweets):
    # key = username, value = number of times they have been mentioned in a tweet
    user_mention_dict = {}
    # initially the dictionary value is an empty list
    # for all tweets
    for tweet in tweets:

        # for each user mentioned in the tweet
        for user in tweet['user_mentions']:

            # get their username/screen name
            mentioned_user = user['screen_name']

            # if the author and the mentioned user are the same:
            if mentioned_user == tweet['user']:
                # move onto the next user mentioned as we do not want to count these as mentions of a user
                continue

            # If the user mentioned is not a key in the dictionary (haven't been mentioned before)
            # then create one for it
            if mentioned_user not in user_mention_dict.keys():
                user_mention_dict[mentioned_user] = 0

            # add 1 to the number of times this user has been mentioned in a tweet
            user_mention_dict[mentioned_user] += 1

    # get a list of the users who have been mentioned
    mentioned_users_sorted = list(user_mention_dict.keys())
    # will now be sorted in descending order in terms of number of mentions
    mentioned_users_sorted.sort(key=lambda x: user_mention_dict[x], reverse=True)

    print("The most popular mentioned users.")
    # if there has been less than 10 users mentioned
    if len(mentioned_users_sorted) < 10:
        # show all of them
        users = len(mentioned_users_sorted)
    else:
        # otherwise just show the top 10
        users = 10

    # for each user mentioned
    for i in range(users):
        # print their username and the number of times they have been mentioned
        print("User = ", mentioned_users_sorted[i], ", No of mentions = ",
              user_mention_dict[mentioned_users_sorted[i]])


''' 
Create a user interaction dict where the user is the key 
and the value is a dict as well with keys=users and vals = frequency of mentions
'''


def create_user_interactions_dict(tweets):
    # key = author of tweet, value = dictionary of users mentioned by the author with key = username, value = frequency
    user_interaction_dict = {}
    number = 0

    # for each tweet
    for tweet in tweets:

        author = tweet['user']

        # if the user isn't in the dict and has mentioned someone in their tweet, then create a key value pair for them
        if author not in user_interaction_dict.keys() and len(tweet["user_mentions"]) > 0:
            user_interaction_dict[author] = {}

        # for each user mentioned in the tweet
        for user in tweet['user_mentions']:

            number += 1

            mentioned_user = user['screen_name']

            # if the author has mentioned themselves, move onto the next user mentioned
            if author == mentioned_user:
                continue

            # if the user mentioned has been mentioned by the author before
            if mentioned_user in user_interaction_dict[author].keys():

                # add 1 to the number of times the user has been mentioned by the tweet author
                user_interaction_dict[author][mentioned_user] += 1

            # otherwise, this is the first time the user has been mentioned by the author
            else:

                # so add the mentioned user to the author's dictionary with frequency 1
                user_interaction_dict[author][mentioned_user] = 1
    print("The number of mentions made is ", number)
    return user_interaction_dict


def write_to_csv(all_tweets):
    with open('tweets.csv', mode='w', encoding='utf-8') as tweet_file:
        tweet_writer = csv.writer(tweet_file, delimiter=',', quotechar='"', newline='', quoting=csv.QUOTE_MINIMAL)
        for tweet in all_tweets:
            tweet_writer.writerow([tweet['id'], tweet['text']])


def get_hashtags_that_appear_together(tweets):
    # this is going to return a dictionary where hashtags are the keys and values are the ones that it appears alongside
    # in tweets
    hashtag_dict = {}
    for tweet in tweets:
        if len(tweet['hashtags']) > 0:
            print(tweet['hashtags'][0]['text'])
            # if there is already a key


# if more than 1 hashtag
# for each tweet
# add the hashtags that appear alongside the first to the hashtag appearance list

def build_retweet_network(retweets):
    # returns a dictionary where the keys are the retweet authors and the value is a dict which has the tweet author and
    # the frequency
    retweet_network = {}
    for retweet in retweets:
        author = retweet['retweeted_user']
        retweeter = retweet['user']
        if author == retweeter:
            continue
        if retweeter not in retweet_network.keys():
            retweet_network[retweeter] = {}
        # if the author has been retweeted before
        if author in retweet_network[retweeter].keys():
            # add 1 to the frequency of them being retweeted by the retweeter
            retweet_network[retweeter][author] += 1
        else:
            retweet_network[retweeter][author] = 1
    return retweet_network


# tweet_interactions = create_user_interactions_dict(normal_tweets)
# retweet_interactions = create_user_interactions_dict(retweets)
# quote_interactions = create_user_interactions_dict(quotes)
#
# print("Numberof Users interacting ")
#
# print("Interactions in tweets")
# print(len(tweet_interactions.keys()))
# print("interactions in RTs")
# print(len(retweet_interactions.keys()))
# print("interactions in Quotes")
# print(len(quote_interactions.keys()))
#
# print()
#
# print("Interactions in tweets")
# all_interactions_list = list(tweet_interactions.items())
# for i in range(10):
#     print(all_interactions_list[i])
# print()
# print("interactions in RTs")
# all_interactions_list = list(retweet_interactions.items())
# for i in range(10):
#     print(all_interactions_list[i])
# print()
# print("interactions in Quotes")
# all_interactions_list = list(quote_interactions.items())
# for i in range(10):
#     print(all_interactions_list[i])

# for each cluster:
# get the most mentioned users
# get the

get_top_mentioned_users(quotes)

# first_cluster = get_tweets_from_cluster(model.labels_, 0, all_tweets)
# second = get_tweets_from_cluster(model.labels_, 1, all_tweets)
# get_top_mentioned_users(all_tweets)
# get_hashtags_that_appear_together(second)

# to get triads
# for each user in the interaction dict
# for each user they have mentioned
# for each user the mentioned user has mentioned
# this is a triad
user_interactions_dict = create_user_interactions_dict(quotes)


def get_triads_and_triangles(user_interactions_dict):
    # returns a list of lists with 3 elements which are the usernames of the users involved
    triads = []
    triangles = []
    for first_user in user_interactions_dict.keys():
        for second_user in user_interactions_dict[first_user].keys():
            if second_user in user_interactions_dict.keys():
                for third_user in user_interactions_dict[second_user].keys():
                    triad = list([first_user, second_user, third_user])
                    triads.append(triad)
                    if third_user in user_interactions_dict.keys():
                        if first_user in user_interactions_dict[third_user].keys():
                            triangles.append(list([first_user, second_user, third_user]))
    return triads, triangles


#
# triads, triangles = get_triads_and_triangles(user_interactions_dict)
# # print(triads[::50])
# print("The number of tweets being analysed for triads is " , len(normal_tweets))
# print("The number of triads is ", len(triads))
# print("The number of triangles is ", len(triangles))

# could get the number of ties between 2 users from the frequency in the user interaction dict

# create a dictionary for retweets with the keys as the authors of the tweets and the values as the retweeted user and
# the frequency possibly

# do the same for the quoted tweet

# could then possibly do it for just mentions in normal tweets - all I need to to is use the
# current get_user_interactions function but just pass in the normal tweets rather than all of them

retweet_network = build_retweet_network(retweets)
for edge in list(retweet_network.items()):
    print(edge)
