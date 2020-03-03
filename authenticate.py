import tweepy


def authenticate():
    auth = tweepy.OAuthHandler('nNeyCLuD02K0DEDeusNdca8qn', 't3TbfjdLJVpGJDoYbrwlVzNgNSitFMVBsept4noFj5rCQlAgnu')
    auth.set_access_token('2695649644-1uVW55xyYtpB046b97yvHaoGk0IdYdD8gh9DaUH',
                          'CXBuA4Oh8MMzUuYNGVrYALgHgU2Yaa2mgFxVF7ITlqas5')
    api = tweepy.API(auth)
    return api
