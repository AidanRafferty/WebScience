from authenticate import authenticate

api = authenticate()


def get_current_trends():
    trends = api.trends_place(id=21125)
    # for i in range(len(trends[0]['trends'])):
    #     print(trends[0]['trends'][i]['name'])
    # print(len(trends[0]['trends']))
    return trends
