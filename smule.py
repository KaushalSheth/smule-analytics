from urllib.parse import unquote
from urllib import request
import json, re, csv
from mutagen.mp4 import MP4, MP4Cover
from .utils import fix_title
from os import path
from .db import saveDBPerformances, saveDBFavorites, fetchDBTitleMappings, dateDelta, fetchDBJoiners, execDBQuery
from datetime import datetime, timedelta, date
from requests_html import HTMLSession, AsyncHTMLSession
import asyncio

DATEFORMAT = '%Y-%m-%dT%H:%M'
CRAWL_SEARCH_OPTIONS = {'contentType':"both",'solo':False,"joins":False}
MYSELF = 'KaushalSheth1'

# Generic method to get various JSON objects for the username from Smule based on the type passed in
def getJSON(username,type="performances",offset=0):
    data = None
    try:
        urlstring = f"https://www.smule.com/{username}/{type}/json?offset={offset}"
        #urlstring = f"https://205.143.41.226/{username}/{type}/json?offset={offset}"
        #print(urlstring)
        with request.urlopen(urlstring) as url:
            data = json.loads(url.read())
    except:
        pass

    return data

# Method to get comments for specified recording
def getComments(web_url):
    print(web_url)
    commentStr = ""
    session = HTMLSession()
    # Get the HTML and render it (apply javascript)
    r = session.get(web_url)
    r.html.render()
    # Get list of users, comments and time of comment (offset from current time)
    usersList = r.html.find('._iap8hd')
    commentsList = r.html.find('._1822wnk')
    timeList = r.html.find('._1gqeov3')
    # Loop through the list and construct comment string (pipe-delimited columns, semi-colon separated lines)
    for i in range(0,len(commentsList)):
        commentStr += f"{timeList[i].text}|{usersList[i].text}|{commentsList[i].text};\n"
    print(commentStr)
    return commentStr.strip(";\n")

# Method to crawl performances of joiners of the specified user
def crawlJoiners(username,mindate='2018-01-01',maxdate='2030-12-31'):
    message = "Crawled the following users: "
    n = "0"
    # Fetch list of joiners from DB
    joiners = fetchDBJoiners(username,mindate,maxdate)
    # Loop through all joiners and fetch their performances.  We will only use the date range, so set other variables to default values
    for j in joiners:
        try:
            u = j['joiner']
            # Fetch the performances for the user and save them
            perf = fetchSmulePerformances(u,9999,0,"performances",mindate,maxdate,searchOptions=CRAWL_SEARCH_OPTIONS)
            m = saveDBPerformances(u,perf)
            # The first word in the message returned indicates the number of favorites processed successfully - save that
            n = m.split()[0]
        except:
            raise
        message += u + " (" + n + "), "
    return message

# Method to crawl favorites/performances for the specified user
# This method assumes a list of performances is already queried and loops through the partners and fetches their favorites/performances and saves them to DB
def crawlUsers(username,performances,maxperf=9999,startoffset=0,mindate='2018-01-01',maxdate='2030-12-31',searchType='favorites'):
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
                perf = fetchSmulePerformances(u,maxperf,startoffset,searchType,mindate,maxdate,searchOptions=CRAWL_SEARCH_OPTIONS)
                m = saveDBPerformances(u,perf)
                # Also save to favories if searchType is favorites
                if searchType =="favorites":
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
def parseEnsembles(username,web_url,parentTitle,titleMappings,mindate='1900-01-01',ensembleMinDate='2020-06-01',searchOptions={}):
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
            responseList = createPerformanceList(username,json.loads(performancesStr),createType="ensemble",parentTitle=parentTitle,titleMappings=titleMappings,mindate=mindate,ensembleMinDate=ensembleMinDate,searchOptions=searchOptions)
            ensembleList = responseList[2]
    except:
        # DEBUG MESSAGE
        print("============")
        print(web_url)
        print("Failed to parse ensembles")
        print("============")
        #raise

    return ensembleList

# Method to extract values from search options
def extractSearchOptions(searchOptions):
    if searchOptions == {}:
        contentType = "both"
        solo = False
        joins = True
    else:
        contentType = searchOptions['contentType']
        solo = searchOptions['solo']
        joins = searchOptions['joins']

    return contentType, solo, joins

# Create performance list out of a performances JSON that is passed in
def createPerformanceList(username,performancesJSON,mindate="1900-01-01",maxdate="2099-12-31",n=0,maxperf=9999,filterType="all",createType="regular",parentTitle="",titleMappings=dict(),ensembleMinDate='2020-06-01',searchOptions={}):
    performanceList = []
    stop = False
    i = n
    contentType, solo, joins = extractSearchOptions(searchOptions)

    # The actual performance data is returned in the "list" JSON object, so loop through those one at a time
    for performance in performancesJSON['list']:
        ct = createType
        perfStatus = performance['perf_status']
        joiners = ""
        partnerHandle = ""

        # As soon as i exceeds the maximum performance value, set the stop variable (for the main loop) and break out of the loop for the current batch
        if i >= maxperf:
            stop = True
            break
        created_at = performance['created_at']
        web_url = f"https://www.smule.com{performance['web_url']}"
        #print(web_url)
        # As soon as created_at is less than the ensemble min date, break out of the loop
        # In case we don't care for joins, then break out as soon as we reach the mindate (no need to process extra days)
        if (created_at < ensembleMinDate) or (not joins and created_at < mindate):
            stop = True
            break
        # If the created_at is greater than the max date, then skip it and proceed with next one
        if created_at > maxdate:
            continue
        #print(f"{i}: {web_url}")
        # If the web_url ends in "/ensembles" then set ct to be "invite"
        if web_url.endswith("/ensembles"):
            ct = "invite"
            # If filterType is Invites, only include the invites that are still open - skip invites where perf_status = "e" (expired)
            if filterType == "invites" and perfStatus == "e":
                # We are now including everything, so technically, this IF block can be removed - leaving it in just so we can easily flip it if needed for a specific use case
                #continue
                pass
        elif filterType == "ensembles" or filterType == "invites":
            # If the performance is not an ensemble, but we specified we want only ensembles or invites, skip the performance and don't increment the count
            continue
        # If created_at is less than the mindate, don't include include it in the performance list, unless it is an ensemble (invite)
        if ((created_at < mindate) and (not ct == "invite")):
            continue
        # Check contentType and skip content if needed - either contentType must be set to "both" or the performance type should be the same as the contentType specified
        if (contentType == "both") or (performance["type"] == contentType):
            pass
        else:
            continue
        # If we're processing ensembles, the parent title will be passed in, so use that to override the performance title because ensemble titles strip out special characters
        if parentTitle == "":
            fixedTitle = fix_title(performance['title'],titleMappings)
        else:
            fixedTitle = parentTitle
        # If possible, we want to set performers to a value other than the username we are searching for
        # We will set the performers to either the partner (if there is any) or to the owner - whichever is not the username
        ownerHandle = performance['owner']['handle']
        ownerId = performance['owner']['account_id']
        owner_pic_url = performance['owner']['pic_url']
        display_user = ownerHandle
        display_pic_url = owner_pic_url
        # Initialize performers to owner - we will overwrite it if we find a partner that is not the same as username
        performers = ownerHandle
        # Initialize list of perfomer IDs and Handles to the owner ID and Handle - we will append other performers to this
        performerIds = str(ownerId)
        performerHandles = ownerHandle
        op = performance['other_performers']
        # Loop through partners and process them
        partnerIndex = 0
        for ptr in op:
            partnerIndex += 1
            partnerId = str(ptr['account_id'])
            partnerHandle = ptr['handle']
            # Append the ID and handle of the partner to the list, but only if both string lengths are still less than 200 (max size of the columns)
            # If MYSELF is the only entry so far, then add the other performer to the front
            if (performerHandles == MYSELF):
                tmpIds = partnerId + "," + performerIds
                tmpHandles = partnerHandle + "," + performerHandles
            else:
                tmpIds = performerIds + "," + partnerId
                tmpHandles = performerHandles + "," + partnerHandle
            if len(tmpIds) <= 200 and len(tmpHandles) <= 200:
                performerIds = tmpIds
                performerHandles = tmpHandles
            partner_pic_url = ptr['pic_url']
            # Set display user and performer to the first partner unless the partner is myself
            if (partnerIndex == 1) and (partnerHandle != MYSELF):
                display_user = partnerHandle
                display_pic_url = partner_pic_url
                performers = partnerHandle
        filename_base = f"{fixedTitle} - {performers}"
        # Set the correct filename extension depending on the performance type m4v for video, m4a for audio
        if performance['type'] == "video":
            filename = filename_base + ".m4v"
        else:
            filename = filename_base + ".m4a"
        pic_filename = filename_base + ".jpg"
        # If we only want solos, skip the performance if performers is not username
        if solo and username != performers:
            continue
        i += 1
        # Once filename is constructed, strip out the "[Short]" from the fixedTitle and set the short_ind accordingly
        if "[Short]" in fixedTitle:
            fixedTitle = fixedTitle.replace(" [Short]","")
            shortInd = "Y"
        else:
            shortInd = "N"
        # Truncate web_url to 300 characters to avoid DB error when saving
        web_url = web_url[:300]
        # It seems like sometimes orig_track_city and few other values are not present - in this case set the them to Unknown
        try:
            orig_track_city = performance['orig_track_city']['city']
            orig_track_country = performance['orig_track_city']['country']
        except:
            orig_track_city = "Unknown"
            orig_track_country = "Unknown"
        try:
            owner_lat = performance['owner']['lat']
            owner_lon = performance['owner']['lon']
        except:
            owner_lat = "0.00"
            owner_lon = "0.00"
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
                'owner_account_id':ownerId,\
                'owner_handle':ownerHandle,\
                'owner_pic_url':owner_pic_url,\
                'display_handle':display_user,\
                'display_pic_url':display_pic_url,\
                'owner_lat':owner_lat,\
                'owner_lon':owner_lon,\
                'filename':filename,\
                'other_performers':op,\
                'performers':performers,\
                'pic_filename':pic_filename,\
                'fixed_title':fixedTitle,\
                'short_ind':shortInd,\
                'partner_name':partnerHandle,\
                'create_type':ct,\
                'perf_status':perfStatus,\
                'expire_at':performance['expire_at'],\
                'joiners':joiners,
                'performer_ids':performerIds,\
                'performer_handles':performerHandles\
                })
        # If any errors occur, simply ignore them - losing some data is acceptable
        except:
            pass
            raise

        # If ct is "invite" and joins flag is True, then process the joins and append to the performance list
        if ct == "invite" and joins:
            ensembleList = parseEnsembles(username,web_url,fixedTitle,titleMappings=titleMappings,mindate=mindate,ensembleMinDate=ensembleMinDate,searchOptions=searchOptions)
            # Only append the joins if the filterType is not Invites.  For Invites, simply concatenate the list of joiners into the joiners string for the invite
            if filterType == "invites":
                for j in ensembleList:
                    joiners += j['partner_name'] + ", "
                joiners = joiners.strip(", ")
                performanceList[-1]['joiners'] = joiners
            else:
                # If there are no matching joins for an invite, remove the invite
                # Also delete the invite if we are only getting solos and the owner is the username
                if ((len(ensembleList) == 0) or (solo and ownerHandle == username)):
                    del performanceList[-1]
                    i -= 1
                # If ensembleList is not empty, add the joins to the performance list
                if len(ensembleList) > 0:
                    performanceList.extend(ensembleList)
                    i += len(ensembleList)

    return [ stop, i, performanceList ]

# Method to fetch Title Mappings from text file
def fetchFileTitleMappings(filename):
    titleMappings = {}
    # First, load the data into a list and sort it by length of the first column
    f = open(filename,'r',encoding='UTF-8')
    fc = csv.reader(f,delimiter="|")
    sfc = sorted(fc, key = lambda row: len(row[1]))
    #sfc = fc
    # Next, loop through the sorted list and build the dict
    for row in sfc:
        #print(row[1])
        titleMappings[row[1]] = row[0]
    return titleMappings

# Method to fetch invites for partners identified by the partner SQL passed in
def fetchPartnerInvites(partnersql,numrows,knowntitles):
    # Since invites typically expire after 7 days, we will set max date to now and mindate to now - 7 days
    currTime = datetime.now()
    mindate = (currTime - timedelta(7)).strftime(DATEFORMAT)
    maxdate = currTime.strftime(DATEFORMAT)
    performanceList = []

    # Fetch list of parnter/title combinations already performed so that we can exclude them from the final list of invites
    performedList = []
    titleList = []
    performedResultset = execDBQuery("select distinct performers || '|' || fixed_title as performed, fixed_title from my_performances")
    for p in performedResultset:
        performedList.append(p['performed'])
        # Build the known title list for use later
        t = p['fixed_title']
        if t not in titleList:
            titleList.append(t)

    # Fetch the list of partners by executing the partnersql query
    partners = execDBQuery(partnersql)
    for ptr in partners:
        # Fetch all invites for the partner
        # Note that next(iter(dict.values())) will return the first column of the query - the assumption is that the first column contains the partner name
        partnerList = fetchSmulePerformances(next(iter(ptr.values())),maxperf=numrows,startoffset=0,type="invites",mindate=mindate,maxdate=maxdate,searchOptions=CRAWL_SEARCH_OPTIONS)
        # Initialize the final list to empty list - we will add net new invtes (not already performed) to it
        finalPartnerList = []
        for p in partnerList:
            t = p['fixed_title']
            # Construct the performed string to match our query above
            performed = p['performers'] + "|" + t
            # As long as this is not on the already performed list, append it to the final list
            if performed not in performedList:
                # Additional check - if knowntitles flag is set, check that the title is in our list of known titles
                if (((knowntitles) and (t in titleList)) or ((not knowntitles) and (t not in titleList))):
                    finalPartnerList.append(p)
        # Extend the peformance list by adding the final partner list to it
        performanceList.extend(finalPartnerList)
        # As soon as we exceed the number of rows specified, break out of the loop
        if (len(performanceList) >= numrows):
            break

    return performanceList

# Method to fetch performances for the specific user upto the max specified
# We arbitrarily decided to default the max to 9999 as that is plenty of performances to fetch
# type can be set to "performances" or "favorites"
def fetchSmulePerformances(username,maxperf=9999,startoffset=0,type="performances",mindate='2018-01-01',maxdate='2030-12-31',searchOptions={}):
    contentType,solo,joins = extractSearchOptions(searchOptions)
    # Smule uses a concept of offset in their JSON API to limit the results returned (currently it returns 25 at a time)
    # It also returns the next offset in case we want to fetch additional results.  Start at 0 and go from there
    next_offset = startoffset
    last_created_date = "2099-12-31"
    # Since ensembles are good for 7 days typically, calculate ensembleMinDate as the minDate - 7 days
    # This will allow us to pick up any new joins for older ensembles
    # If mindate only has date and no time, append 00:00 for time so that strptime does not fail
    if len(mindate) == 10:
        mindate += "T00:00"
    else:
        mindate = mindate.replace(" ","T")
    ensembleMinDate = (datetime.strptime(mindate,DATEFORMAT) - timedelta(7)).strftime(DATEFORMAT)
    # We use i to keep track of how many performances we have fetched so far, and break out of the loop when we reach the maxperf desired
    i = 0
    # Iinitialize all other variables used in the method
    stop = False
    performanceList = []
    #titleMappings = fetchDBTitleMappings()
    titleMappings = fetchFileTitleMappings('TitleMappings.txt')
    # When the last result page is received, next_offset will be set to -1, so keep processing until we get to that state
    while next_offset >= 0:
        print(f"======== {username} {contentType} {next_offset} {i} {stop} {maxperf} {last_created_date} =======")
        # Get the next batch of results from Smule
        if type == "ensembles" or type == "invites":
            fetchType = "performances"
        else:
            fetchType = type
        performances = getJSON(username,fetchType,next_offset)
        if performances == None:
            break
        for performance in performances['list']:
            last_created_date = performance['created_at']
        responseList = createPerformanceList(username,performances,mindate,maxdate,i,maxperf,type,titleMappings=titleMappings,ensembleMinDate=ensembleMinDate,searchOptions=searchOptions)

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
def downloadSong(web_url,baseFolder,file,performance,username):
    # Construct full path to filename
    filename = baseFolder + file
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
            #print(web_url)
            # First get the HTML for the web_url
            htmlstr = str(url.read())

            # Next, parse out the actual media_url, which is in the content field of the "twitter:player:stream" object
            # We need to strip out the "amp;" values and convert the "+" value to URL-friendly value
            media_url = unquote(re.search('twitter:player:stream.*?content=".*?"',htmlstr).group(0).split('"')[2]).replace("amp;","").replace("+","%2B")

            # Print out the media_url for debugging purposes
            # TODO: Convert this to a debug message?
            #print(media_url)

            # Open the file in binary write mode and write the data from the media_url
            f = open(filename,'w+b')
            f.write(request.urlopen(media_url).read())
            f.close()
    except:
        print("FAILED TO DOWNLOAD!!!!!!!!!!!!!!")
        #raise
        return 0

    try:
        # Calculate necessary dates
        createdat = performance["created_at"]
        perfdate = datetime.strptime(createdat[0:10],"%Y-%m-%d")
        # Set the album date to the start of the week on which the song was created
        albumdate = (perfdate - timedelta(days=perfdate.weekday())).strftime("%Y-%m-%d")
        albumyear = createdat[0:4]
        # Write the tags for the M4A file
        af = MP4(filename)
        af["\xa9nam"] = performance["fixed_title"]
        af["\xa9ART"] = performance["performers"]
        # Set Album Artist to the username we searched for
        af["aART"] = username
        # Android seems to have a bug where wrong art is displayed if "Album" tag is empty so set it to "Smule" followed by current date
        af["\xa9alb"] = f"Smule - {albumdate}"
        af["\xa9day"] = f"{albumyear}"
        af["purd"] = createdat
        af["\xa9cmt"] = f"Performed on {createdat}"

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
