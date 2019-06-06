from urllib import request
from urllib.parse import unquote
import json, re

def getJSON(username,type="performances",offset=0):
    urlstring = f"https://www.smule.com/{username}/{type}/json?offset={offset}"
    with request.urlopen(urlstring) as url:
        data = json.loads(url.read())

    return data

def fetchSmulePerformances(username,maxperf=9999):
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
            try:
                performanceList.append({\
                    'key':performance['key'],\
                    'type':performance['type'],\
                    'created_at':performance['created_at'],\
                    'title':performance['title'],\
                    'artist':performance['artist'],\
                    'ensemble_type':performance['ensemble_type'],\
                    'child_count':performance['child_count'],\
                    'app_uid':performance['app_uid'],\
                    'arr_key':performance['arr_key'],\
                    'orig_track_city':performance['orig_track_city']['city'],\
                    'orig_track_country':performance['orig_track_city']['country'],\
                    'media_url':performance['media_url'],\
                    'video_media_url':performance['video_media_url'],\
                    'video_media_mp4_url':performance['video_media_mp4_url'],\
                    'web_url':web_url,\
                    'cover_url':performance['cover_url'],\
                    'total_performers':performance['stats']['total_performers'],\
                    'total_listens':performance['stats']['total_listens'],\
                    'total_loves':performance['stats']['total_loves'],\
                    'total_comments':performance['stats']['total_comments'],\
                    'total_commenters':performance['stats']['total_commenters'],\
                    'performed_by':performance['performed_by'],\
                    'performed_by_url':performance['performed_by_url'],\
                    'owner_account_id':performance['owner']['account_id'],\
                    'owner_handle':performance['owner']['handle'],\
                    'owner_pic_url':performance['owner']['pic_url'],\
                    'owner_lat':performance['owner']['lat'],\
                    'owner_lon':performance['owner']['lon'],\
                    'filename':filename\
                    })
            except:
                pass
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

