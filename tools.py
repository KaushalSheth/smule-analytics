import asyncio
from bs4 import BeautifulSoup
from pyppeteer import launch
import os, time
from .db import execDBQuery, saveDBTitleMetadata
from .smule import fetchUserFollowing
from urllib import request
import json, re, csv
from statistics import mode
import discogs_client
from fuzzywuzzy import process, fuzz
import requests

# Set global variables using env file
DISCOGS_TOKEN = os.environ.get('DISCOGS_TOKEN', default='')
discogsClient = discogs_client.Client('SmuleAnalytics/1.0', user_token=DISCOGS_TOKEN)

async def loadDynamicHtml(url):
    global htmlstr
    # Launch the browser
    browser = await launch(handleSIGINT=False,handleSIGTERM=False,handleSIGHUP=False)
    # Open a new browser page
    page = await browser.newPage()
    # Open the url passed in the newly created page (tab)
    await page.goto(url)
    # Since the page has lazy loading, wait 2 seconds, then scroll to bottom to load more data - do this 3 times in order yo get upto 100 performances (25 per page)
    time.sleep(2)
    await page.evaluate("""{window.scrollBy(0, document.body.scrollHeight);}""")
    time.sleep(2)
    await page.evaluate("""{window.scrollBy(0, document.body.scrollHeight);}""")
    time.sleep(2)
    await page.evaluate("""{window.scrollBy(0, document.body.scrollHeight);}""")
    time.sleep(2)
    htmlstr = await page.content()
    # Close browser
    await browser.close()

    return htmlstr

# Get Title Metadata
def titleMetadata(utilitiesOptions):
    track = utilitiesOptions['title'].replace("+"," ")
    list1 = [searchDiscogsTitle(track)]
    return {"list1":list1,"list2":[]}

# Search Discogs for title Metadata
def searchDiscogsTitle(track):
    #discogsReleases = discogsClient.search(track=f'"{track}"')
    discogsReleases = discogsClient.search(track=track)
    i = 0
    maxRatio = 0
    titleRec = {}
    stop = False
    # Loop through releases to check for a track with the best match
    for r in discogsReleases:
        i += 1
        # Loop through the tracks in the release to find the best one
        for t in r.tracklist:
            ratio = fuzz.ratio(track, t.title)
            if (ratio > maxRatio) and (len(t.artists) > 0):
                maxRatio = ratio
                # Construct artist string
                artist = ""
                for a in t.artists:
                    artist += a.name + ", "
                # Strip trailing comma and replace last comma with &
                artist = ' &'.join(artist.strip(", ").rsplit(',',1))
                titleRec = {"fixed_title":track,"meta_title":t.title,"artist":artist,"duration":t.duration,"score":ratio}
                if (maxRatio >= 95):
                    stop = True
                    break
        if stop or i > 10:
            break
    print(f"{i}: {titleRec}")
    return titleRec

# Save metadata for all titles missing metadata in DB
def saveTitleMetadata():
    titleMetadataList = []
    # Loop through all titles missing metadata
    sqlquery = """
        with titles as (select distinct fixed_title from my_performances)
        select  t.fixed_title
        from    titles t
                left outer join title_metadata tm on tm.fixed_title = t.fixed_title
        where   tm.fixed_title is null
        -- limit 50
        """
    titleList = execDBQuery(sqlquery)
    i = 0
    for t in titleList:
        print(t)
        md = searchDiscogsTitle(t['fixed_title'])
        if not md:
            md = {"fixed_title":t['fixed_title'],"meta_title":"","artist":"","duration":"","score":0}
            #print(md)
        titleMetadataList.append(md)
        i += 1
        if i % 5 == 0:
            saveDBTitleMetadata(titleMetadataList)
            titleMetadataList = []
    saveDBTitleMetadata(titleMetadataList)

    return {"list1":titleMetadataList,"list2":[]}

# Method to fetch recording metadata from musicbrainz
def getRecordingMetadataJSON(titleInput):
    data = None
    urltitle = titleInput.replace(" ","+")
    urlstring = f"https://musicbrainz.org/ws/2/recording?query={urltitle}&fmt=json"
    #urlstring = f"https://www.smule.com/search/by_type?q=KaushalSheth1&type=recording&sort=recent&offset=0&size=0"
    titleRow = ""
    try:
        with request.urlopen(urlstring) as url:
            data = json.loads(url.read())
    except:
        # Ignore any errors
        print("Error fetching recording metadata")
        pass
    if data != None:
        # Loop through all the recordings to determine the most popular artist
        artistList = []
        i = 0
        for r in data['recordings']:
            # Get score, title, and length from 1st recording
            if i == 0:
                score = r['score']
                title = r['title']
                # Sometimes, length is not available - in that case keep the previous value
                try:
                    length = round(r['length']/1000.0/60.0,2)
                except:
                    length = 0
            i += 1
            # If score >= 100, check artists
            if score >= 100:
                artist = ""
                for a in r['artist-credit']:
                    artist += a['name']
                    #print(artist)
                    if 'joinphrase' in a.keys():
                        artist += a['joinphrase']
                artistList.append(artist)
        #print(artistList)
        artist = mode(artistList)
        titleRow = f"Input = {titleInput}; Score = {score}; Title = {title}; Length = {length} minutes; Artist = {artist}"
        #print(titleRow)
    return titleRow

def findHtmlElements(htmlstr,element="p",name="dummy"):
    # Process HTML string with BeautifulSoup
    soup = BeautifulSoup(htmlstr,features="lxml")
    element_list = []
    # Generate an element list using search parameters provided
    # Setup the search
    for e in soup.find_all(element,name):
        element_list.append(e.get_text())
    # Remove duplicates
    final_list = list(set(element_list))

    return final_list

def titlePerformers(utilitiesOptions):
    title = utilitiesOptions["title"]
    sort = utilitiesOptions["sort"]
    print(f"Title = {title}")
    url = f"https://www.smule.com/search?q={title}&type=recording&sort={sort}"
    try:
        loop = asyncio.get_running_loop()
    except:
        loop = asyncio.new_event_loop()
    htmlstr = loop.run_until_complete(loadDynamicHtml(url))
    owner_list = findHtmlElements(htmlstr,"span","profile-name-text")
    joiner_list = findHtmlElements(htmlstr,"span","profile-name handle")

    return {"list1":owner_list,"list2":joiner_list}

def nonJoiners(utilitiesOptions):
    title = "Non-Joiners"
    non_joiner_list = []
    sqlquery = """
        select  performers,
                count(*) as perf_cnt,
                extract(day from current_timestamp - min(created_at)) as days_since_first_perf,
                count(case when join_ind = 1 then 1 else null end) as join_cnt,
                extract(day from current_timestamp - max(case when join_ind = 1 then created_at else null end)) as days_since_last_join
        from    my_performances
        group by performers
        """
    partnerStats = execDBQuery(sqlquery)
    userFollowing = fetchUserFollowing('KaushalSheth1')
    for u in userFollowing:
        psList = [d for d in partnerStats if d['performers'] == u['handle']]
        ps = psList[0] if psList else {}
        #ps = next(item for item in partnerStats if item["performers"] == u['handle'])
        try:
            #if ((ps["join_cnt"] == 0 or ps["days_since_last_join"] > 365) and ps["days_since_first_perf"] > 265):
            if ((ps["join_cnt"] == 0 or ps["days_since_last_join"] > 180) and ps["days_since_first_perf"] > 180):
            #if ((ps["join_cnt"] == 0 or ps["days_since_last_join"] > 180) and ps["days_since_first_perf"] > 90 and ps["perf_cnt"] < 5):
                non_joiner_list.append(f"{ps['performers']} ({ps['perf_cnt']}, {ps['days_since_first_perf']}, {ps['join_cnt']}, {ps['days_since_last_join']})")
        except:
            pass
    return {"list1":non_joiner_list,"list2":[]}

def getHtml(utilitiesOptions):
    url = utilitiesOptions["url"]
    try:
        loop = asyncio.get_running_loop()
    except:
        loop = asyncio.new_event_loop()
    htmlstr = loop.run_until_complete(loadDynamicHtml(url))

    return {"owners":[htmlstr],"joiners":[]}

# Download performer images
def downloadPics(utilitiesOptions):
    # Iniitalize variables
    basefolder = '/tmp/'
    picswhereclause = utilitiesOptions["picswhereclause"]
    picCnt = 0
    # Fetch pic URLs from DB
    sqlquery = f"""
        with
            pics as (select performers as pic_handle, display_pic_url as pic_url, min(created_at) min_time from my_performances where {picswhereclause} group by 1,2)
        select *, row_number() over(partition by pic_handle order by min_time) as pic_nbr from pics
        """
    pics = execDBQuery(sqlquery)
    # Loop through each image and save it
    for p in pics:
        picHandle = p['pic_handle']
        picUrl = p['pic_url']
        picNbr = p['pic_nbr']
        filename = basefolder + picHandle + "-" + f'{picNbr:03}' + '.jpg'
        # If the file already exists, skip it
        if os.path.exists(filename):
            #print(f"ALREADY EXISTS - {filename}")
            continue
        else:
            f = open(filename,'wb')
            f.write(requests.get(picUrl).content)
            f.close()
            picCnt += 1
    return picCnt

# The remaining code was copied from Stack Overflow and modified - https://stackoverflow.com/questions/71514124/find-near-duplicate-and-faked-images
from sentence_transformers import SentenceTransformer, util
from PIL import Image
import glob
import os

def processDuplicateImages(utilitiesOptions):
    print("Processing duplicates")
    dupCount = 0
    wildcard = utilitiesOptions['picswildcard']
    dupesfolder = utilitiesOptions['dupesfolder']
    # Load the OpenAI CLIP Model
    print('Loading CLIP Model...')
    model = SentenceTransformer('clip-ViT-B-32')

    # Next we compute the embeddings
    # To encode an image, you can use the following code:
    # from PIL import Image
    # encoded_image = model.encode(Image.open(filepath))
    image_names = list(glob.glob(wildcard))
    if len(image_names) == 0:
        return 0
    print("Images:", len(image_names))
    encoded_image = model.encode([Image.open(filepath) for filepath in image_names], batch_size=128, convert_to_tensor=True, show_progress_bar=True)

    # Now we run the clustering algorithm. This function compares images aganist
    # all other images and returns a list with the pairs that have the highest
    # cosine similarity score
    processed_images = util.paraphrase_mining_embeddings(encoded_image)

    # =================
    # SIMILAR IMAGES
    # =================
    #print('Finding similar images...')
    # Use a threshold parameter to identify two images as similar. By setting the threshold lower,
    # you will get larger clusters which have less similar images in it. Threshold 0 - 1.00
    # A threshold of 1.00 means the two images are exactly the same. Since we are finding near
    # duplicate images, we can set it at 0.99 or any number 0 < X < 1.00.
    threshold = 0.97
    similar_images = [image for image in processed_images if image[0] >= threshold]

    for score, image_id1, image_id2 in similar_images:
        #print("\nScore: {:.3f}%".format(score * 100))
        #print(image_names[image_id1])
        #print(image_names[image_id2])
        dupe_image = image_names[image_id2]
        # Set moveto name to the dupes folder + the last part of the dupe_image, which should be the filename
        moveto_image = dupesfolder + dupe_image.split("\\")[-1]
        # Since the file might have already been moved, ignore any errors during move
        try:
            os.rename(dupe_image,moveto_image)
            dupCount += 1
        except:
            print(f"Could not find {dupe_image}")
            pass
    return dupCount
