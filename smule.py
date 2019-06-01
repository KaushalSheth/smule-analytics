from urllib import request
from urllib.parse import unquote
import json, re

def getJSON(username,type="performances",offset=0):
    urlstring = f"https://www.smule.com/{username}/{type}/json?offset={offset}"
    with request.urlopen(urlstring) as url:
        data = json.loads(url.read())

    return data

def parsePerformances(username,maxperf=9999):
    next_offset = 0
    i = next_offset
    stop = False
    while next_offset >= 0:
        performances = getJSON(username,"performances",next_offset)
        for performance in performances['list']:
            i += 1
            print(f"# = {next_offset+i}")
            title = performance['title']
            owner = performance['owner']['handle']
            print(f"Title = {title}")
            print(f"Created At = {performance['created_at']}")
            print(f"Owner = {owner}")
            web_url = f"https://www.smule.com{performance['web_url']}"
            print(f"Web URL = {web_url}")
            filename = f"{title} - {owner}.m4a"
            # downloadSong(web_url,filename)
            print("=====")
            if i >= maxperf:
                stop = True
                break
        if stop:
            break
        else:
            next_offset = performances['next_offset']

def fetchPerformances(username,maxperf=9999):
    next_offset = 0
    i = next_offset
    stop = False
    performanceList = []
    while next_offset >= 0:
        performances = getJSON(username,"performances",next_offset)
        for performance in performances['list']:
            i += 1
            performanceList.append({\
                    'key':performance['key'],\
                    'title':performance['title'],\
                    'owner':performance['owner']['handle'],\
                    'created_at':performance['created_at'],\
                    'city':f"{performance['orig_track_city']['city']}, {performance['orig_track_city']['country']}",\
                    'web_url':f"https://www.smule.com{performance['web_url']}"\
                    })
            if i >= maxperf:
                stop = True
                break
        if stop:
            break
        else:
            next_offset = performances['next_offset']
    return performanceList

def downloadSong(web_url,filename):
    with request.urlopen(web_url) as url:
        htmlstr = str(url.read())
        media_url = unquote(re.search('twitter:player:stream.*?content=".*?"',htmlstr).group(0).split('"')[2]).replace("amp;","").replace("+","%2B")
        print(media_url)
        f = open(filename,'w+b')
        f.write(request.urlopen(media_url).read())
        f.close()

