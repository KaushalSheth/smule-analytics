from urllib import request
from urllib.parse import unquote
import json, re

# Generic method to get various JSON objects for the username from Smule based on the type passed in
def getJSON(username,type="performances",offset=0):
    urlstring = f"https://www.smule.com/{username}/{type}/json?offset={offset}"
    with request.urlopen(urlstring) as url:
        data = json.loads(url.read())

    return data

# The title field we get from Smule for performances contains many letters and words that are not appropriate for the filename
# Fix the title to remove/replace these so that we can use this "fixed" title in the filename
def fix_title(title):
    # Define translation table to translate all graphical letters to actual letters, and strip out all the symbols
    ttable = title.maketrans(\
            '🅅🅓🅳🅉🄱ℍ🅀ℚ🅙🅧🅒🅗🅤🅡🅐🄷🅄🄼🅂🄰🄵🄰🅁🅂🄷🄾🅁🅃🆂🅷🅾🆁🆃🄲🄷🄰🄸🄽🄺🄳🅃🄴🄻🄶🄿🅴🅷🆀🅺🆄🅲🅷🅾🆁🅸🅶🅸🅽🅰🅻🅱ⓓⓗⓐⓓⓚⓐⓝⒹ【】🄹🅈',\
            'VDDZBQHQJXCHURAHUMSAFARSHORTSHORTCHAINKDTELGPEHQKUCHORIGINALBdhadkanD[]JY',\
            '🎸🕺👈🎼😘/”“🦁⚜️🕉️⏯️🇭🇩🌙"<>[]|💚💖🇸🌸🌻🤪🇭🇴🇷🇹👉💜🐝🍀✔💕💝♥🌹☔🌧️🌩️🌦️🙈™💑®@🎧📝🌷🍁🍂🍃🌼💗👀🤫👑💑🌟🎤💙⚘🙄❤#💗™💘🤹😍💟💞🔥😇🤩😏ᴴᴰȺ💃🎈=😔'\
            )

    # Do the translation, conver to uppercase temporarily, create standard format for [Short], remove all unnecessary words, convert to mixed case
    result = title.translate(ttable).\
            upper().\
            replace('[HD]','').\
            replace('(HD)','').\
            replace('HD','').\
            replace('{{SHORT}}','[SHORT]').\
            replace('{SHORT}','[SHORT]').\
            replace('((SHORT))','[SHORT]').\
            replace('(SHORT)','[SHORT]').\
            replace('SHORT_2','[SHORT]').\
            replace('SHORT_3','[SHORT]').\
            replace('SHORT','[SHORT]').\
            replace('[[SHORT]]','[SHORT]').\
            replace('JEX','').\
            replace('[HQ]','').\
            replace('(HQ)','').\
            replace('HQ','').\
            replace('[M]','').\
            replace('[T]','').\
            replace('[BEST]','').\
            replace('[F]','').\
            replace('(CLEAN TRACK)','').\
            replace('D MAJOR','').\
            replace('(DUET)','').\
            replace('(FULL SONG)','').\
            replace('(100%PURE)','').\
            replace('[CLEAN DUET]','').\
            replace('100%','').\
            replace('[FULL]','').\
            replace('(CRYSTAL CLEAR)','').\
            replace('[ORIGINAL MUSIC]','').\
            replace('HQTRACK!!','').\
            replace('CLEAR','').\
            replace('COVER','').\
            replace('OST','').\
            replace('🄷🅀','').\
            replace('🇭🇩','').\
            replace('{}','').\
            title()

    # If [Short] is anywhere in the name, remove it and add it to the end of the title
    if "[Short]" in result:
        result = (result.replace("[Short]","") + " [Short]").strip().replace('[ ]','')

    # Strip any leading/trailing whitespace, remove any leading "-", and if the name contains any "-", strip anything after the first "-" (remove movie names)
    result = result.strip().lstrip('-').split("-")[0].strip()

    return result

# Method to fetch performances for the specific user upto the max specified
# We arbitrarily decided to default the max to 9999 as that is plenty of performances to fetch
def fetchSmulePerformances(username,maxperf=9999):
    # Smule uses a concept of offset in their JSON API to limit the results returned (currently it returns 25 at a time)
    # It also returns the next offset in case we want to fetch additional results.  Start at 0 and go from there
    next_offset = 0
    # We use i to keep track of how many performances we have fetched so far, and break out of the loop when we reach the maxperf desired
    i = next_offset
    # Iinitialize all other variables used in the method
    stop = False
    performanceList = []

    # When the last result page is received, next_offset will be set to -1, so keep processing until we get to that state
    while next_offset >= 0:
        # Get the next batch of results from Smule
        performances = getJSON(username,"performances",next_offset)

        # The actual performance data is returned in the "list" JSON object, so loop through those one at a time
        for performance in performances['list']:
            i += 1
            title = fix_title(performance['title'])
            # Initialize performers to the handle of the owner, and then append the handle of the first other performer to it
            performers = performance['owner']['handle']
            op = performance['other_performers']
            if len(op) > 0:
                performers += " and " + op[0]['handle']
            # TODO: If there is more than one other performer, do we wish to include in the filename?
            filename = f"{title} - {performers}.m4a"
            web_url = f"https://www.smule.com{performance['web_url']}"
            try:
                ## Append the relevant performance data from the JSON object (plus the variables derived above) to the performance list
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
            # If any errors occur, simply ignore them - losing some data is acceptable
            except:
                pass
            # As soon as i exceeds the maximum performance value, set the stop variable (for the main loop) and break out of the loop for the current batch
            if i >= maxperf:
                stop = True
                break
        # If step variable is set, break out of the main loop, otherwise, set the next_offset so we can fetch the next batch
        if stop:
            break
        else:
            next_offset = performances['next_offset']
    return performanceList

# Download the specified web_url to the filename specified
def downloadSong(web_url,filename):
    # The web_url returns an HTML page that contains the link to the content we wish to download
    with request.urlopen(web_url) as url:
        # First get the HTML for the web_url
        htmlstr = str(url.read())

        # Next, parse out the actual media_url, which is in the content field of the "twitter:player:stream" object
        # We need to strip out the "amp;" values and convert the "+" value to URL-friendly value
        media_url = unquote(re.search('twitter:player:stream.*?content=".*?"',htmlstr).group(0).split('"')[2]).replace("amp;","").replace("+","%2B")

        # Print out the media_ul for debuggin purposes
        # TODO: Convert this to a debug message?
        print(media_url)

        # Open the file in binary write mode and write the data from the media_url
        f = open(filename,'w+b')
        f.write(request.urlopen(media_url).read())
        f.close()

