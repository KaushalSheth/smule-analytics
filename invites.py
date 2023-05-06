from os import path
from .constants import *
from .utils import fix_title, build_comment, printTs
from .db import saveDBPerformances, saveDBFavorites, fetchDBTitleMappings, dateDelta, fetchDBJoiners, execDBQuery, saveDBSingerFollowing, saveDBGeoCache, fetchDBUserFollowing
from .smule import fetchSmulePerformances, getPartnerInfo
from datetime import datetime, timedelta, date
from requests_html import HTMLSession, AsyncHTMLSession
import random

# Method to fetch invites for partners identified by the partner SQL passed in
def fetchSongInvites(inviteOptions,numrows):
    dayslookback = inviteOptions['dayslookback']
    currTime = datetime.now()
    mindate = (currTime - timedelta(dayslookback)).strftime(DATEFORMAT)
    maxdate = currTime.strftime(DATEFORMAT)
    i = 0
    maxperf = inviteOptions['maxperf']
    title = inviteOptions['title']
    inclpartner = inviteOptions['inclpartner']
    print(f"************************  {title}")
    performanceList = []
    qtype = "recording"
    # Set search query based on whether or not title is specified. If it is, search for recordings of that title sung by favorite partners. Else. search for invites of that title by anyone
    if title == "":
        # Fetch list of songs not sung this month
        #sqlquery = "select fixed_title from favorite_song where current_month_ind = 0 order by adj_weighted_cnt desc"
        sqlquery = "select fixed_title as fixed_title, replace(fixed_title,' ','+') as search_string from favorite_song where current_month_ind = 0 order by random()"
        qtype = "active_seed"
    elif inclpartner:
        # Fetch list of qualifying partners and append to title being searched for
        sqlquery = f"select '{title}' as fixed_title, replace('{title}',' ','+')||'+'||partner_name as search_string from favorite_partner where last10_five_cnt = last10_rating_cnt order by recency_score desc"
    else:
        # Do a search only for the title specified
        sqlquery = f"select '{title}' as fixed_title, replace('{title}',' ','+') as search_string"
    songList = execDBQuery(sqlquery)
    # Loop through each song, and fetch open invites for it
    for s in songList:
        # Fetch n invites for the song
        t = s['fixed_title']
        songInvites = fetchSmulePerformances(s['search_string'],maxperf=maxperf,startoffset=0,type=qtype,mindate=mindate,maxdate=maxdate,searchOptions=CRAWL_SEARCH_OPTIONS)
        found = False
        numPerf = 0
        # Loop through the resulting list and append the appropriate entries to performanceList
        for s in songInvites:
            if s['fixed_title'] == t:
                found = True
                numPerf += 1
                performanceList.append(s)
        # If at least one performance was found for the song, increment our song counter
        if found:
            i += 1
            printTs(f"-- {i}: {numPerf} invites for {t}")
            # Break out of the loop when numrows is reached
            if i >= numrows:
                break
    return performanceList

# Method to fetch invites for partners identified by the partner SQL passed in
def fetchPartnerInvites(inviteOptions,numrows):
    # Define a function to process a partner list to build a performance list for the number of rows specified
    def createList(partners,numrows,checkstop=False):
        # Define all the non-local variables to inherit from parent method
        nonlocal i,followingAccountIds,inviteOptions,performedList,titleList,knowntitles,newtitles,unknowntitles,repeats,notfollowing,numPerf,stopScore,stopHandle,currMonthTitles

        # Edge case - if numrows = 0 then exit method immediately or number of performances is already at the max
        if (numrows == 0) or (numPerf >= numrows):
            return

        # Define constants used in this method
        MAX_KNOWN = inviteOptions['maxknown']
        MAX_UNKNOWN = inviteOptions['maxunknown']
        # Since invites typically expire after 7 days, we will set max date to now and mindate to now - 5 days (to give some buffer before it expires)
        currTime = datetime.now()
        mindate = (currTime - timedelta(5)).strftime(DATEFORMAT)
        maxdate = currTime.strftime(DATEFORMAT)

        partnerSort = stopScore
        printTs(f"# Partners = {len(partners)}")
        partnerHandle = ""
        # Loop through the partner list and process it
        for ptr in partners:
            partnerHandle = list(iter(ptr.values()))[0]
            partnerAccountId = list(iter(ptr.values()))[1]
            partnerSort = list(iter(ptr.values()))[2]
            joinCount = int(list(iter(ptr.values()))[3])
            recentJoinCount = int(list(iter(ptr.values()))[5])

            # Break out of loop if partnerSort is higher than the stopScore (only if we are checking stop score)
            if (checkstop and ((partnerSort > stopScore) or (stopHandle == partnerHandle))):
                break

            isFollowing = partnerAccountId in followingAccountIds
            # If the "notfollowing" option is set (true) then only include partners I'm not following.  Otherwise, only include partners I'm following.
            # If the conditions are not met, skip this partner and process next one
            if ( (notfollowing and isFollowing) or (not notfollowing and not isFollowing) ):
                printTs(f"--- NOT FOLLOWING {partnerHandle}")
                continue
            # Fetch all invites for the partner
            partnerInvites = fetchSmulePerformances(partnerHandle,maxperf=numrows,startoffset=0,type="active_seed",mindate=mindate,maxdate=maxdate,searchOptions=CRAWL_SEARCH_OPTIONS)
            # Initialize the final list to empty list - we will add net new invtes (not already performed) to it
            finalPartnerInvites = []
            knownCount = 0
            unknownCount = 0
            # Add appropriate indicators to the partnerInvites for use later
            for p in partnerInvites:
                t = p['fixed_title']
                ptrTitle = p['performers'] + "|" + t
                isRepeat = any(p['performed'] == ptrTitle for p in performedList)
                if isRepeat:
                    rptLastTime = [p['last_time'] for p in performedList if p['performed'] == ptrTitle][0]
                else:
                    rptLastTime = ""
                isUnknown = (t not in titleList)
                isNewTitle = not any(ct['fixed_title'] == t for ct in currMonthTitles)
                # Append appropriate indicators to title
                if isRepeat:
                    p['title'] += f" (RPT:{rptLastTime})"
                if isUnknown:
                    p['title'] += " (UNKNOWN)"
                if isNewTitle:
                    p['title'] += " (NEW)"
                p['isRepeat'] = isRepeat
                p['isUnknown'] = isUnknown
                p['isNotNewTitle'] = not isNewTitle

            # Sort partner list in random order
            #sortedPartnerInvites = random.sample(partnerInvites,len(partnerInvites))
            # Sort partner list by created timestamp (oldest first)
            sortedPartnerInvites = sorted(partnerInvites, key=lambda k: f"{k['isNotNewTitle']} {k['created_at']}")
            # Loop through the sorted partenr list
            for p in sortedPartnerInvites:
                #print(f"{p['isNotNewTitle']} {p['isRepeat']} {p['created_at']} {p['fixed_title']}")
                # Extract the calculated flags and delete them from list as they are not meant to be part of performanceList
                isRepeat = p['isRepeat']
                isUnknown = p['isUnknown']
                isNewTitle = not p['isNotNewTitle']
                del p['isRepeat']
                del p['isUnknown']
                del p['isNotNewTitle']
                # If only new titles are allowed, skip this row if it is not a new title
                if (newtitles and not isNewTitle):
                    #print(f"Skipped - {p['title']}")
                    continue
                # We will include the performance only if repeats are allowed or if the performance is not in the list of already performed performances
                if (repeats or not isRepeat):
                    # We will include known/unknown titles based on options set
                    if ( (knowntitles and not isUnknown) or (unknowntitles and isUnknown) ):
                        # We want a maximum of 1 Unknown title from each partner (if any are allowed), so continue to next title if that max is reached
                        if isUnknown:
                            unknownCount += 1
                            if unknownCount > MAX_UNKNOWN:
                                continue
                        else:
                            knownCount += 1
                        # Store join count in "Total_listens" field, and last 10 ratings field in "total_loves"
                        p['total_listens'] = joinCount
                        # p['total_loves'] = partnerSort
                        p['total_loves'] = getPartnerInfo("partner_name",p['performers'],"last10_rating_str")
                        # Update the join_cnt and recent_join_count values to use the partner values
                        p['join_cnt'] = joinCount
                        p['recent_join_cnt'] = recentJoinCount
                        finalPartnerInvites.append(p)
                        # We will limit each partner to MAX_INVITES invites, so break out of loop when count reaches or exceeds this value
                        if knownCount >= MAX_KNOWN:
                            break
            # Extend the peformance list by adding the final partner list to it
            performanceList.extend(finalPartnerInvites)
            i += 1
            # If the number of performances changes, then update the variable and print out a message indicating how many performances were added
            if (numPerf != len(performanceList)):
                numPerf = len(performanceList)
                printTs(f"-- {i}: {numPerf} after {partnerHandle} - {knownCount + unknownCount} / {len(partnerInvites)} ({partnerSort})")
            # As soon as we exceed the number of rows specified, break out of the loop
            if (numPerf >= numrows):
                break
        # Keep track of the score at which to stop for second run
        stopScore = partnerSort
        stopHandle = partnerHandle
        return

    # Extract relevent parametrs from invite options
    partnerchoice = inviteOptions['partnerchoice']
    partnersql = inviteOptions['partnersql']
    knowntitles = inviteOptions['knowntitles']
    unknowntitles = inviteOptions['unknowntitles']
    repeats = inviteOptions['repeats']
    notfollowing = inviteOptions['notfollowing']
    newtitles = inviteOptions['newtitles']
    performanceList = []
    # If neither known or unknown titles is set, just return with empty list because there will be no matches
    if (not knowntitles) and (not unknowntitles):
        return performanceList
    # Get list of handles of users I'm following
    followingAccountIds = fetchDBUserFollowing()
    # print(followingAccountIds)
    # return performanceList

    # Fetch list of parnter/title combinations already performed so that we can exclude them from the final list of invites
    # Limit to only last 18 months - if performance older than that, it is ok to repeat
    titleList = []
    printTs(f"{datetime.now().strftime('%H:%M:%S')} Querying performedList")
    performedSQL = "select performers || '|' || fixed_title as performed, fixed_title, to_char(max(created_at),'YYYY-MM-DD') as last_time from my_performances where created_at > current_timestamp - interval '18 months' group by 1,2"
    # Debugging SQL below - comment out above line and uncomment below line for debugging
    #performedSQL = "select 'a|b' as performed, 'b' as fixed_title, '2020-01-01' as last_time"
    performedList = execDBQuery(performedSQL)
    for p in performedList:
        # Build the known title list for use later
        t = p['fixed_title']
        if t not in titleList:
            titleList.append(t)

    # Get list of titles performed this month
    printTs(f"{datetime.now().strftime('%H:%M:%S')} Querying currMonthTitles")
    currTitlesSQL = "select distinct fixed_title from my_performances where to_char(created_at,'YYYYMM') = to_char(current_timestamp,'YYYYMM')"
    # Debugging SQL below - uncomment it to override above SQL
    #currTitlesSQL = "select 'x' as fixed_title"
    currMonthTitles = execDBQuery(currTitlesSQL)

    # Initialize counters
    i = 0
    numPerf = 0
    stopScore = 999999
    stopHandle = ""

    # Fetch the list of partners by executing the partnersql query.  Create reversed list as well to support some of the choices
    # Debugging SQL below - uncomment it to override above SQL
    #partnersql = "select performed_by as partner_name, account_id as partner_account_id, 9999 as recency_score, 0 as join_cnt, pic_url as display_pic_url, 0 as recent_join_cnt from singer where performed_by ilike 'OfficiallyDiva'"
    printTs(f"{datetime.now().strftime('%H:%M:%S')} Querying partners")
    partnersTop = execDBQuery(partnersql)

    printTs(f"{datetime.now().strftime('%H:%M:%S')} Processing partners")
    partnersBottom = partnersTop[::-1]
    # Set the Max rows for Top list
    if partnerchoice.startswith("split"):
        # Skip Top
        topRows = 0
        # Construct a list to use for processing split partners
        # First, determine the pslit point based on the choice
        if partnerchoice == "splitmiddle":
            splitPoint = int(len(partnersTop)/2)
        # If bad split choice is sent in, do a random split
        else:
            splitPoint = random.randint(0,len(partnersTop))
        printTs(f"SplitPoint = {splitPoint} / {len(partnersTop)}")
        # Construct one list from middle to bottom (mb) and one reversed list from middle to top (mt)
        mb = partnersTop[splitPoint:]
        mt = partnersTop[splitPoint-1::-1]
        # Interleave the mt and mb lists so we basically start from the middle and work towards the top and bottom alternately
        partnersSplit = []
        lt = len(mt)
        lb = len(mb)
        for i in range(max(lb,lt)):
            if i < lt:
                partnersSplit.append(mt[i])
            if i < lb:
                partnersSplit.append(mb[i])
    elif partnerchoice == "top":
        topRows = numrows
    elif partnerchoice == "bottom":
        topRows = 0
    elif partnerchoice == "random":
        topRows = numrows
        random.shuffle(partnersTop)

    # If we chose to process partners from the middle out, don't need to process top and bottom separately
    if (partnerchoice.startswith("split")):
        print("============= PROCESSING MIDDLE PARTNERS ==============")
        createList(partnersSplit,numrows,False)
    else:
        # Otherwise, call the createList method for the top rows; next call it using the reversed list and the total number of rows to fill in the remainder
        print("============= PROCESSING TOP PARTNERS ==============")
        createList(partnersTop,topRows,False)
        print("============= PROCESSING BOTTOM PARTNERS ==============")
        createList(partnersBottom,numrows,True)
    return performanceList
