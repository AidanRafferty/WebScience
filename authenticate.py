import tweepy


def authenticate():
    auth = tweepy.OAuthHandler('', '')
    auth.set_access_token('','')
    api = tweepy.API(auth)
    return api
