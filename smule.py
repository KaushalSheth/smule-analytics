from urllib import request
from urllib.parse import unquote
import json, re

def getJSON(username,type="performances",offset=0):
    urlstring = f"https://www.smule.com/{username}/{type}/json?offset={offset}"
    with request.urlopen(urlstring) as url:
        data = json.loads(url.read())

    return data

def fetchPerformances(username,maxperf=9999):
    next_offset = 0
    i = next_offset
    stop = False
    performanceList = []
    while next_offset >= 0:
        performances = getJSON(username,"performances",next_offset)
        for performance in performances['list']:
            i += 1
            title = performance['title']
            owner = performance['owner']['handle']
            filename = f"{title} - {owner}.m4a"
            web_url = f"https://www.smule.com{performance['web_url']}"
            performanceList.append({\
                    'key':performance['key'],\
                    'title':title,\
                    'type':performance['ensemble_type'],\
                    'owner':owner,\
                    'filename':filename,\
                    'created_at':performance['created_at'],\
                    'city':f"{performance['orig_track_city']['city']}, {performance['orig_track_city']['country']}",\
                    'web_url':web_url\
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

