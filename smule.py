from urllib import request
from urllib.parse import unquote
import json, re
from mutagen.mp4 import MP4, MP4Cover
from .utils import fix_title
from os import path
from .db import saveDBPerformances, saveDBFavorites

# Generic method to get various JSON objects for the username from Smule based on the type passed in
def getJSON(username,type="performances",offset=0):
    urlstring = f"https://www.smule.com/{username}/{type}/json?offset={offset}"
    print(urlstring)
    with request.urlopen(urlstring) as url:
        data = json.loads(url.read())

    return data

# Method to crawl favorites for the specified user
# This method assumes a list of performances is already queried and loops through the partners and fetches their favorites and saves them to DB
def crawlFavorites(username,performances,maxperf=9999,startoffset=0,mindate='2018-01-01',maxdate='2030-12-31'):
    message = "Crawled the following users: "
    # Save the original performance list
    orig_performances = performances

    try:
        # Loop through all the performances to build a list of users to crawl
        userList = []
        for p in performances:
            # Get performers string and split into individual users
            performers = p['performers'].split(" and ")
            # For each user in the list add to the list of users unless it is the same as the username passed in or it already exists in teh list
            for u in performers:
                if (u != username) and (u not in userList):
                    userList.append(u)
        # Loop through the users and process each one individually
        for u in userList:
            try:
                # Fetch the performances for the user and save them
                perf = fetchSmulePerformances(u,maxperf,startoffset,"favorites",mindate,maxdate)
                m = saveDBPerformances(u,perf)
                m = saveDBFavorites(u,perf)
                # The first word in the message returned indicates the number of favorites processed successfully - save that
                n = m.split()[0]
            except:
                raise
            message += u + " (" + n + "), "

        # Remove the last comma
        message = message.rstrip(", ")

    # If any exceptions happen, simply ignore it so that the golbal performances can be set back to the original value and return
    except:
        raise

    performances = orig_performances
    return message

# Parse ensembles from the specified web_url and return an ensembles list that can be appended to the performances list
def parseEnsembles(username,web_url,fixedTitle):
    ensembleList = []

    try:
        # The web_url returns an HTML page that contains the link to the content we wish to download
        with request.urlopen(web_url) as url:
            # First get the HTML for the web_url
            htmlstr = str(url.read())
            # Next, parse the HTML to extract the JSON string for performances
            performancesBytes = bytes(re.search('"performances":(.*?"next_offset":.*?})',htmlstr).group(1),'latin')
            performancesStr = performancesBytes.decode('utf8')
            #print(performancesStr)
            # We need to strip out all special characters that are represented as hex values because the json.loads method does not like them
            performancesStr = re.sub(r'"\[HQ\]"','', re.sub(r'\\''','', (re.sub(r'\\x..', '', performancesStr ))))
            # Process the performanceJSON and construct the ensembleList
            responseList = createPerformanceList(username,json.loads(performancesStr),createType="ensemble",fixedTitle=fixedTitle)
            ensembleList = responseList[2]
    except:
        # DEBUG MESSAGE
        print("============")
        print(performancesStr)
        print("Failed to parse ensembles")
        raise

    return ensembleList

# Create performance list out of a performances JSON that is passed in
def createPerformanceList(username,performancesJSON,mindate="1900-01-01",maxdate="2099-12-31",n=0,maxperf=9999,filterType="all",createType="regular",fixedTitle=""):
    performanceList = []
    stop = False
    i = n

    # The actual performance data is returned in the "list" JSON object, so loop through those one at a time
    for performance in performancesJSON['list']:
        ct = createType
        perfStatus = performance['perf_status']

        # As soon as i exceeds the maximum performance value, set the stop variable (for the main loop) and break out of the loop for the current batch
        if i >= maxperf:
            stop = True
            break
        created_at = performance['created_at']
        # As soon as created_at is less than the min date, break out of the loop
        if created_at < mindate:
            stop = True
            break
        # If the created_at is greater than the max date, then skip it and proceed with next one
        if created_at > maxdate:
            continue
        web_url = f"https://www.smule.com{performance['web_url']}"
        #print(f"{i}: {web_url}")
        # If the web_url ends in "/ensembles" then set ct to be "invite"
        if web_url.endswith("/ensembles"):
            ct = "invite"
            # If filterType is Invites, only include the invites that are still open - skip invites where perf_status = "e" (expired)
            if filterType == "invites" and perfStatus == "e":
                #continue
                pass
        elif filterType == "ensembles" or filterType == "invites":
            # If the performance is not an ensemble, but we specified we want only ensembles or invites, skip the performance and don't increment the count
            continue
        i += 1
        # If we're processing ensembles, the fixed title will be passed in, so use that to override the performance title because ensemble titles strip out special characters
        if fixedTitle == "":
            title = fix_title(performance['title'])
        else:
            title = fixedTitle
        # Initialize performers to the handle of the owner, and then append the handle of the first other performer to it
        owner = performance['owner']['handle']
        display_user = owner
        owner_pic_url = performance['owner']['pic_url']
        display_pic_url = owner_pic_url
        performers = owner
        op = performance['other_performers']
        # TODO: If there is more than one other performer, do we wish to include in the filename?
        if len(op) > 0:
            partner = op[0]['handle']
            partner_pic_url = op[0]['pic_url']
            performers += " and " + partner
            # If the owner is the username we are processing, switch the display user to the first other performer
            if owner == username:
                display_user = partner
                display_pic_url = partner_pic_url
        filename_base = f"{title} - {performers}"
        filename = filename_base + ".m4a"
        pic_filename = filename_base + ".jpg"
        # Truncate web_url to 300 characters to avoid DB error when saving
        web_url = web_url[:300]
        # It seems like sometimes orig_track_city is not present - in this case set the city and country to Unknown
        try:
            orig_track_city = performance['orig_track_city']['city']
            orig_track_country = performance['orig_track_city']['country']
        except:
            orig_track_city = "Unknown"
            orig_track_country = "Unknown"
        # Try appending the performance to the list and ignore any errors that occur
        try:
            ## Append the relevant performance data from the JSON object (plus the variables derived above) to the performance list
            performanceList.append({\
                'key':performance['key'],\
                'type':performance['type'],\
                'created_at':created_at,\
                'title':performance['title'],\
                'artist':performance['artist'],\
                'ensemble_type':performance['ensemble_type'],\
                'child_count':performance['child_count'],\
                'app_uid':performance['app_uid'],\
                'arr_key':performance['arr_key'],\
                'orig_track_city':orig_track_city,\
                'orig_track_country':orig_track_country,\
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
                'owner_handle':owner,\
                'owner_pic_url':owner_pic_url,\
                'display_handle':display_user,\
                'display_pic_url':display_pic_url,\
                'owner_lat':performance['owner']['lat'],\
                'owner_lon':performance['owner']['lon'],\
                'filename':filename,\
                'other_performers':op,\
                'performers':performers,\
                'pic_filename':pic_filename,\
                'fixed_title':title,\
                'partner_name':performers,\
                'create_type':ct,\
                'perf_status':perfStatus,\
                'expire_at':performance['expire_at']\
                })
        # If any errors occur, simply ignore them - losing some data is acceptable
        except:
            pass
            raise

        # If ct is "invite" then process the joins and append to the performance list
        if ct == "invite" and filterType != "invites":
            ensembleList = parseEnsembles(username,web_url,title)
            performanceList.extend(ensembleList)
            i += len(ensembleList)

    return [ stop, i, performanceList ]

# Method to fetch performances for the specific user upto the max specified
# We arbitrarily decided to default the max to 9999 as that is plenty of performances to fetch
# type can be set to "performances" or "favorites"
def fetchSmulePerformances(username,maxperf=9999,startoffset=0,type="performances",mindate='2018-01-01',maxdate='2030-12-31'):
    # Smule uses a concept of offset in their JSON API to limit the results returned (currently it returns 25 at a time)
    # It also returns the next offset in case we want to fetch additional results.  Start at 0 and go from there
    next_offset = startoffset
    # We use i to keep track of how many performances we have fetched so far, and break out of the loop when we reach the maxperf desired
    i = 0
    # Iinitialize all other variables used in the method
    stop = False
    performanceList = []
    # When the last result page is received, next_offset will be set to -1, so keep processing until we get to that state
    while next_offset >= 0:
        print(f"======== {next_offset} {i} {stop} {maxperf} =======")
        # Get the next batch of results from Smule
        if type == "ensembles" or type == "invites":
            fetchType = "performances"
        else:
            fetchType = type
        performances = getJSON(username,fetchType,next_offset)
        responseList = createPerformanceList(username,performances,mindate,maxdate,i,maxperf,type)

        # The createPerformanceList method returns a list which contains the values for stop, i and performanceList as the 3 elements (in that order)
        stop = responseList[0]
        i = responseList[1]
        # Add each element of the returned list of performances to the performanceList variable
        performanceList.extend(responseList[2])

        # If step variable is set, break out of the main loop, otherwise, set the next_offset so we can fetch the next batch
        if stop:
            break
        else:
            next_offset = performances['next_offset']
    return performanceList

# Download the specified web_url to the filename specified; return 1 if downloaded or 0 if failed/exists
def downloadSong(web_url,filename,performance):
    # Print filename
    print("========================")
    print(filename)

    # If the file already exists, skip it
    if path.exists(filename):
        print("ALREADY EXISTS")
        return 0

    try:
        # The web_url returns an HTML page that contains the link to the content we wish to download
        with request.urlopen(web_url) as url:
            # Print out the web_url for debugging purposes
            # TODO: Convert to debug message?
            print(web_url)
            # First get the HTML for the web_url
            htmlstr = str(url.read())

            # Next, parse out the actual media_url, which is in the content field of the "twitter:player:stream" object
            # We need to strip out the "amp;" values and convert the "+" value to URL-friendly value
            media_url = unquote(re.search('twitter:player:stream.*?content=".*?"',htmlstr).group(0).split('"')[2]).replace("amp;","").replace("+","%2B")

            # Print out the media_url for debugging purposes
            # TODO: Convert this to a debug message?
            print(media_url)

            # Open the file in binary write mode and write the data from the media_url
            f = open(filename,'w+b')
            f.write(request.urlopen(media_url).read())
            f.close()
    except:
        print("FAILED TO DOWNLOAD!!!!!!!!!!!!!!")
        return 0

    try:
        # Write the tags for the M4A file
        af = MP4(filename)
        af["\xa9nam"] = performance["title"]
        af["\xa9ART"] = performance["performers"]
        # Android seems to have a bug where wrong art is displayed is "Album" tag is empty so set it to "Smule"
        af["\xa9alb"] = "Smule"
        af["purd"] = performance["created_at"]

        # Write the JPEG to the M4A file as album cover
        pic_url = performance['display_pic_url']
        img = MP4Cover(request.urlopen(pic_url).read(), imageformat=MP4Cover.FORMAT_JPEG)
        af["covr"] = [img]

        # Save the updated tags to the file
        af.save()
    except:
        print("FAILED TO UPDATE TAGS!!!")
        return 0

    # Print pic URL for debugging purposes
    # print(pic_url)
    return 1
