from urllib import request
from urllib.parse import unquote
import json, re

def getJSON(username,type="performances",offset=0):
    urlstring = f"https://www.smule.com/{username}/{type}/json?offset={offset}"
    with request.urlopen(urlstring) as url:
        data = json.loads(url.read())

    return data

def fix_title(title):
    # Define translation table to translate all graphical letters to actual letters, and strip out all the symbols
    ttable = title.maketrans(\
            '🅙🅧🅒🅗🅤🅡🅐🄷🅄🄼🅂🄰🄵🄰🅁🅂🄷🄾🅁🅃🆂🅷🅾🆁🆃🄲🄷🄰🄸🄽🄺🄳🅃🄴🄻🄶🄿🅴🅷🆀🅺🆄🅲🅷🅾🆁🅸🅶🅸🅽🅰🅻🅱ⓓⓗⓐⓓⓚⓐⓝⒹ【】🄹🅈',\
            'JXCHURAHUMSAFARSHORTSHORTCHAINKDTELGPEHQKUCHORIGINALBdhadkanD[]JY',\
            '💕💝♥🌹☔🌧️🌩️🌦️🙈™💑®@🎧📝🌷🍁🍂🍃🌼💗👀🤫👑💑🌟🎤💙⚘🙄❤#💗™💘🤹😍💟💞🔥😇🤩😏ᴴᴰȺ💃🎈=😔'\
            )

    # Do the translation, conver to uppercase temporarily, create standard format for [Short], remove all unnecessary words, convert to mixed case
    result = title.translate(ttable).\
            upper().\
            replace('((SHORT))','[SHORT]').\
            replace('(SHORT)','[SHORT]').\
            replace('SHORT','[SHORT]').\
            replace('[[SHORT]]','[SHORT]').\
            replace('[HD]','').\
            replace('(HD)','').\
            replace('HD','').\
            replace('JEX','').\
            replace('[HQ]','').\
            replace('(HQ)','').\
            replace('HQ','').\
            replace('[M]','').\
            replace('[T]','').\
            replace('[BEST]','').\
            replace('[F]','').\
            replace('(CLEAN TRACK)','').\
            replace('(DUET)','').\
            replace('(100%PURE)','').\
            replace('[CLEAN DUET]','').\
            replace('100%','').\
            replace('[FULL]','').\
            replace('{}','').\
            replace('(CRYSTAL CLEAR)','').\
            replace('[ORIGINAL MUSIC]','').\
            replace('HQTRACK!!','').\
            replace('CLEAR','').\
            replace('COVER','').\
            replace('OST','').\
            replace('🄷🅀','').\
            title()

    # If [Short] is anywhere in the name, remove it and add it to the end of the title
    if "[Short]" in result:
        result = (result.replace("[Short]","") + " [Short]").strip().replace('[ ]','')

    # Strip any leading/trailing whitespace, remove any leading "-", and if the name contains any "-", strip anything after the first "-" (remove movie names)
    result = result.strip().lstrip('-').split("-")[0].strip()

    return result

def fetchSmulePerformances(username,maxperf=9999):
    next_offset = 0
    i = next_offset
    stop = False
    performanceList = []
    while next_offset >= 0:
        performances = getJSON(username,"performances",next_offset)
        for performance in performances['list']:
            i += 1
            title = fix_title(performance['title'])
            performers = performance['owner']['handle']
            op = performance['other_performers']
            if len(op) > 0:
                performers += " and " + op[0]['handle']
            filename = f"{title} - {performers}.m4a"
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
                    'filename':filename,\
                    'other_performers':op\
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

