from urllib import request
from urllib.parse import unquote
import json, re

def getJSON(username,type="performances",offset=0):
    urlstring = f"https://www.smule.com/{username}/{type}/json?offset={offset}"
    with request.urlopen(urlstring) as url:
        data = json.loads(url.read())

    return data

def parsePerformances(username):
    next_offset = 0
    while next_offset >= 0:
        performances = getJSON(username,"performances",next_offset)
        i = 0
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
            downloadSong(web_url,filename)
            print("=====")
        next_offset = performances['next_offset']
        break

def downloadSong(web_url,filename):
    with request.urlopen(web_url) as url:
        htmlstr = str(url.read())
        media_url = unquote(re.search('twitter:player:stream.*?content=".*?"',htmlstr).group(0).split('"')[2]).replace("amp;","").replace("+","%2B")
        print(media_url)
        f = open(filename,'w+b')
        f.write(request.urlopen(media_url).read())
        f.close()

