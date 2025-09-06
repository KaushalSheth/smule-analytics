import re
import random
from datetime import datetime
from .constants import *
import json, re, csv
from urllib import request
from fake_useragent import UserAgent

# COMMENTS = {\
#     'awesome':['awesome performance 👌👌👌👌👌','amazing singing 👌👌👌👌👌','awesome rendition 👌👌👌👌👌'],\
#     'fantastic':['fantastic performance 👌👌👌👌','fabulous rendition 👌👌👌👌','excellent singing 👌👌👌👌'],\
#     'good':['superb singing 👌👌👌','beautiful performance 👌👌👌','great rendition 👌👌👌'],\
#     'average':['lovely singing 👌👌','lovely performance 👌👌','lovely rendition 👌👌'],\
#     'ok':['nice rendition 👌','nicely sung 👌','nice performance 👌'],\
#     'bad':['good attempt']
#     }

rating1 = []
rating1.append("Great effort! 👌 Karaoke is about fun and you nailed that part. Keep practicing!")
rating1.append("Brave performance! 👌 Your energy was wonderful. A little practice and you will be unstoppable!")
rating1.append("Fantastic energy! 👌 You clearly love music. Keep working and you will see amazing progress!")
rating1.append("Fun performance! 👌 You made me smile. Keep practicing and you will get stronger!")
rating2 = []
rating2.append("Good effort with melody! 👌👌 Singing improving and you are finding your rhythm!")
rating2.append("Well done staying with beat! 👌👌 Your vocal control is coming along. Right track!")
rating2.append("Nice work stayijng in tune! 👌👌 Your voice has potential and you are controlling it better!")
rating2.append("Good job with pacing! 👌👌 Your confidence is growing and it shows in your singing!")
rating2.append("Solid attempt! 👌👌 Getting more comfortable with the microphone and its paying off!")
rating2.append("You are developing style! 👌👌 Voice sounded stronger in parts. Keep working on it!")
rating3 = []
rating3.append("Nice performance! 👌👌👌 Hit most notes and kept good rhythm. Voice really developing!")
rating3.append("Good job overall! 👌👌👌 Pitch was solid and you stayed with music well. Confident!")
rating3.append("Well done! 👌👌👌 Voice sounded clear and handled challenging parts nicely. Great!")
rating3.append("Solid singing! 👌👌👌 Maintained good control and performance was engaging!")
rating3.append("Nice work! 👌👌👌 Timing was good and you hit the high notes well. Finding groove!")
rating3.append("Good performance! 👌👌👌 Voice has nice tone and you are comfortable performing!")
rating3.append("You did well! 👌👌👌 Rhythm was steady and you sang with confidence. Improving!")
rating3.append("Nice job! 👌👌👌 Handled melody smoothly and voice projected well. Great foundation!")
rating3.append("Good singing! 👌👌👌 Stayed on key mostly and your energy was perfect. Keep going!")
rating3.append("Well performed! 👌👌👌 Voice control was good and you engaged audience nicely!")
rating4 = []
rating4.append("Excellent performance! 👌👌👌👌 Voice was strong and clear. You really connected with song!")
rating4.append("Outstanding job! 👌👌👌👌 Pitch was spot-on and performance was captivating!")
rating4.append("Fantastic singing! 👌👌👌👌 You nailed difficult parts and voice had great emotion!")
rating4.append("Wonderful performance! 👌👌👌👌 Control was excellent and you made the song your own!")
rating4.append("Great job! 👌👌👌👌 Voice sounded professional and you hit every note with confidence!")
rating4.append("Impressive singing! 👌👌👌👌 Rhythm was perfect and voice had beautiful tone. Natural!")
rating4.append("Excellent work! 👌👌👌👌 You commanded audience and vocal technique was strong!")
rating4.append("Outstanding performance! 👌👌👌👌 Voice was powerful and expressive. Brought song to life!")
rating4.append("Fantastic job! 👌👌👌👌 Pitch control was excellent and performance was magnetic!")
rating4.append("Wonderful singing! 👌👌👌👌 Voice had great range and you performed with real artistry!")
rating5 = []
rating5.append("Absolutely perfect! 👌👌👌👌👌 Voice was flawless and performance was mesmerizing!")
rating5.append("Incredible performance! 👌👌👌👌👌 You sang like a professional and captivated me!")
rating5.append("Phenomenal! 👌👌👌👌👌 Voice control was perfect and delivered every note with precision!")
rating5.append("Outstanding! 👌👌👌👌👌 You transformed the song and made it uniquely yours!")
rating5.append("Brilliant execution! 👌👌👌👌👌 Voice was pitch-perfect and performance magnetic!")
rating5.append("Spectacular! 👌👌👌👌👌 Hit every note flawlessly and performed with incredible emotion!")
rating5.append("Perfect execution! 👌👌👌👌👌 Voice was powerful and beautiful. Natural-born performer!")
rating5.append("Exceptional! 👌👌👌👌👌 Vocal range and control were impressive. Truly professional!")
rating5.append("Magnificent! 👌👌👌👌👌 Voice soared and you connected with me. Breathtaking!")
rating5.append("Flawless! 👌👌👌👌👌 Performance was captivating start to finish. Incredible talent!")

COMMENTS = {'awesome':rating5,'fantastic':rating4,'good':rating3,'average':rating2,'ok':rating1,'bad':['good attempt']}

# Generate a fake user agent to avoid Smule blocking python requests
def createFakeUAHeaders(acceptEncoding="none"):
    global HEADERS
    try: HEADERS
    except NameError:
        #ua = UserAgent()
        #HEADERS = {'User-Agent':ua.random}
        HEADERS = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': acceptEncoding,
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Priority': 'u=0, i',
            'Cookie': '_ga=GA1.1.1256643851.1747455776; smule_autoplay={%22enabled%22:true}; py={%22globalVolume%22:true%2C%22volume%22:0.5}; _fbp=fb.1.1747516498143.732750319145640822; smule_cookie_banner_disabled=true; L=N; smule_consent={%22cookieBannerVersionValue%22:2%2C%22acceptedCookies%22:[%22marketing%22%2C%22functionality%22]}; smule_production_refresh=eyJyZWZyZXNoX3Rva2VuIjoicjJfX0RNWGNWL3ZBcitQZ1pHSlZTeldqSk4yRGJMK29TWCtxMngyTXoyTXZyMXVnL25JNXU5VkZhU1g0ZzEvU2hZMTlvLzJFRkJ4bVFWbVBaOVNNcDZ4NDg4UzNGYnlGSkR3ZjBWV3krWDU2ZmJlQmFHSGpTbWxIZkhta2hWZHlpVk1hVVFoTjRsZkx0SDQxRGdia0ppYmpNU2QvVTkxdVhVTT0iLCJleHBpcmVfYXQiOiIyMDI1LTEwLTA4VDAxOjU0OjQ2Ljk4NFoifQ%3D%3D--f7a55b2f1ee6868c01bddbe609ad734e0a571898; _smule_session=eyJzZXNzaW9uX2lkIjoiNDgyOTIyMjFiMDZmMjg0MmYyYmYxZjkwMTBlYTk4ZGMiLCJfY3NyZl90b2tlbiI6IjFzNHhTQnAxT09SNXQ0eGRTSGprYk9QV1dUU05pUFR6S2xFTXFzRzI4dm89IiwidXNlcl9pZCI6MTc5MjM0NTgyNiwic211bGVpZF9zZXNzaW9uIjoiZzRfNl9WazRZTmk4TG0wckJ5NzVaR3RZVDYyaXBnV0Q5YnZrcjVZdjRYL2MwMUs3akYzcTUwWHllV3kzVkEvNWFXUXh2Iiwic2Vzc2lvbl90dGwiOiIyMDI1LTA4LTA3VDE4OjI0OjQ2LjAwMFoiLCJ1c2VyX2hhbmRsZSI6IkthdXNoYWxTaGV0aDEiLCJ1c2VyX2VtYWlsIjoiZmFjZWJvb2tAc2hldGgubmFtZSIsInVzZXJfcGljX3VybCI6Imh0dHBzOi8vYy1jZG5ldC5jZG4uc211bGUuY29tL3NtdWxlLWdnLXV3MS16LTEvYWNjb3VudC9waWN0dXJlL2EyLzAzL2QyZDI2MmQ4LTAyZjktNDczOC04Mjk2LTRjYzM1YjM5MzViNS5qcGciLCJ1c2VyX3BsYXllcl9pZCI6MTc5MjM3MDcxNSwiamlkIjoiMTc5MjM0NTgyNkBqYy5zbXVsZS5jb20iLCJ4bXBwX2hvc3RzIjpbImpjLnNtdWxlLmNvbSJdLCJleHBpcmVfYXQiOjE3NTk4ODg0ODYwMDB9--9b70d9c9e87591d93f7e2320d6ce21538f151d9f; smule_id_production=eyJ3ZWJfaWQiOiJmYWYyNmE2ZC1kYWZlLTRmNzMtOWFjOS1hZWEzMzliMzgwOTMiLCJkYXVfdHMiOjE3NTQzNTg0NzIsInNlc3Npb25faWQiOiJnNF84X0VXWm45ZlNyOG5nMXFHVDZFM2xNUDh6emlGTDJRZVluUmdmeFpueHllSUphaEs4MVZkdHVGdz09IiwicGxheWVyX2lkIjozNDM3ODAyNzY0fQ%3D%3D--27aabab9ad6ad32065b13d69fd1ca00a6b6020ca; _ga_3HLCN2KDGH=GS2.1.s1754358472$o81$g1$t1754359805$j60$l0$h0'
            }
    #print(HEADERS)
    return HEADERS

# Print the specified message prefixed by current timestamp
def printTs(message):
    print(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " " + message)

# Build comment dictionary by randomly selecting a comment for each category
def build_comment(prefix="",suffix=""):
    comment = {\
        'awesome':prefix + random.choice(COMMENTS['awesome']) + suffix,\
        'fantastic':prefix + random.choice(COMMENTS['fantastic']) + suffix,\
        'good':prefix + random.choice(COMMENTS['good']) + suffix,\
        'average':prefix + random.choice(COMMENTS['average']) + suffix,\
        'ok':prefix + random.choice(COMMENTS['ok']) + suffix\
        }
    return comment

# Generic method to get various JSON objects for the username from Smule based on the type passed in
def getJSON(username="",type="recording",offset=0,version="legacy",sort="recent",cursor="start"):
    data = None
    try:
        if version == "legacy":
            urlstring = f"https://www.smule.com/{username}/{type}/json?offset={offset}"
        elif type == "following":
            urlstring = f"https://www.smule.com/api/profile/followees?accountId={username}&offset={offset}&limit=25"
        elif type == "pinworthy":
            urlstring = f"https://www.smule.com/api/playlists/aplist/view?playlistKey=1792345826_21679136&cursor={cursor}"
        else:
            urlstring = f"https://www.smule.com/api/search/byType?q={username}&type={type}&sort={sort}&offset={offset}&size=0"
        #print(urlstring)
        req = request.Request(urlstring,headers=createFakeUAHeaders())
        with request.urlopen(req) as url:
            perfJSON = url.read()
            #print(perfJSON)
            data = json.loads(perfJSON)
    except:
        # Ignore any errors
        printTs("Error fetching JSON")
        raise
        pass
    return data

# The title field we get from Smule for performances contains many letters and words that are not appropriate for the filename
# Fix the title to remove/replace these so that we can use this "fixed" title in the filename
def fix_title(title,titleMappings):
    # Define translation table to translate all graphical letters to actual letters, and strip out all the symbols
    ttable = title.maketrans(\
            'Ⓙʲᶠ𝐟𝐌Ĵ𝗔𝗲𝗵𝗼𝗞𝗥ᵤₑₜ𝐦𝐀𝐩𝐧𝐚𝐁𝐞𝐤𝐢𝐊𝐬ᵇ𝓐𝓭𝓷𝓪⑥⑤④⓪ˣ𝙃𝘿⁵③⑦ⒾⒺⓘⓔʍǟⒸⓟⓙⓃ𝐮𝐥ᴜɪᴍᴋʟᴀH𝐐𝐅u𝐋𝑯𝑫ᴼαηⒼⓀⓜⒷⓑⒽⓉⒽⓌⓕⒻⓛᴄoᴠᴇrᵖᵀᴹᵈⁱᵍⁱᵗᵃˡⓏᶻᵘⓩ𝗦𝗮𝗻𝗺𝗣u𝗿𝗶𝗨𝗘𝗧ⓎⒶⓐⓨⁿⓅᵐD𝐔𝐄𝐓𝗙𝘂𝗹𝗹𝗛𝗗𝐎🆂🅷Ⓞ🆁🆃🅦ʰᴮᵉˢᵗᶜᵒᵛᵉʳＳＨＯＲＴᴅᴾᴸᴳᴱᑕᗰᑎ🅚Ⓢⓤ𝔻𝕀𝔾Sʜᴏʀᴛ🆅ⓦⓖᎥᑭƳᖇᗪ　𝑺Fϙ𝕾𝒉𝒐𝒓𝒕🅟🅔🆆🇲🇫ÅåȟȋJᒎᗷᕼᗩ𝔖𝐡𝐨𝐫𝐭ᵁᴺᵂᴵ𝐇𝐃🄷🅀🆇🅿🆉ᴿ🇶Ⓡ🅠🇪🇱🇦🇬🅖🅜🅢🅗🅞🅡🅣ⓔⓘ🅹🅵🄷🅀ⓢⓗⓞⓡⓣ🅕🅤🅛🅛ᴴᴰ🇭🇩🇸🅝🇭🇴🇷🇹🅑🅘🇼🄷🅀🇰🇦🇺🇳🅢🆈🅼🅆🅅🅓🅳🅉🄱ℍ🅀ℚ🅙🅧🅒🅗🅤🅡🅐🄷🅄🄼🅂🄰🄵🄰🅁🅂🄷🄾🅁🅃🆂🅷🅾🆁🆃🄲🄷🄰🄸🄽🄺🄳🅃🄴🄻🄶🄿🅴🅷🆀🅺🆄🅲🅷🅾🆁🅸🅶🅸🅽🅰🅻🅱ⓓⓗⓐⓓⓚⓐⓝⒹ【】🄹🅈',\
            'JJFFMJAEHOKRUETMAPNABEKIKSBADNA6540XHD537IEIEMACPJNULUIMKLAHQFULHDOANGKMBBHTHWFFLCOVERPTMDIGITALZZUZSANMPURIUETYAAYNPMDUETFULLHDOSHORTWHBESTCOVERSHORTDPLGECMNKSUDIGSHORTVWGIPYRD SFQSHORTPEWMFAAHIJJBHASHORTUNWIHDHQXPZRQRQELAGGMSHORTEIJFHQSHORTFULLHDHDSNHORTBIWHQKAUNSYMWVDDZBQHQJXCHURAHUMSAFARSHORTSHORTCHAINKDTELGPEHQKUCHORIGINALBdhadkanD[]JY',\
            '√✶⭕👻☘❇✳😞⚧💲🧛🐣🏽😜💍☂👧~🪔🔱🔵💅🙌♫💊👮😰⏭⏮🧶✫🌋😆⚔☾✮☆🐈🎂👠👞👡¶🤟😁🏃🔯💫🤷🍻🐞😐🛫☑📀🆑🪁🔐🆘💪😈▲💢🔝🤘〘〙🇲♧🚩🐅²👼🍒🍷📿*►🦂🦢📼⏩🍄¹🤭♣࿐😭🏠😌😥❉🦋🤝♪🔰💐³༒🌝👁😻🏇🚴🧚🎨☜🎹🎵🧡😃🌈°🏝⛱🌄💿💏🇮🇳🎶✌️👬🌾▶️◀️🖐✊😋✅🎊🎆🌴🐧♾️😢😪🖤💌🙃💓🙇‍♀️🌺​⏏️☞📌🎭🐎☺️★👱🙅‍♂️🕊+🌧⛈🌨🇦🇼🇦🇨🕸👩‍❤️‍👨❣️🔊😉💯👸😎🌃📚😊👩🏻🤗⚡‍💼🎀❌❤💛🥀😗👍🎻✿●•🎞💦🇨🇻🌖💎🌜⭐🌛👩✨😙💔–@🙏☛☚▫💋🏼‍♂♀👌!.❄🎷🗿👫🔘💥🎙©🆕️☄🚶🚶🤔🥰🎸🕺👈🎼😘/”“🦁⚜️🕉️⏯️🌙"|💚💖🌸🌻🤪👉💜🐝🍀✔💕💝♥🌹☔🌧️🌩️🌦️🙈™💑®@🎧📝🌷🍁🍂🍃🌼💗👀🤫👑💑🌟🎤💙⚘🙄❤#💗™💘🤹😍💟💞🔥😇🤩😏Ⱥ💃🎈=😔'\
            )
    # Do the translation and convert to uppercase temporarily
    r1 = title.translate(ttable).upper()

    # Standardize all versions of "short" to "`Short`"
    r2 = standardize_short(r1,'`','`')

    # Remove brackets
    r3 = remove_brackets_spaces(r2)

    # Remove unnecessary words
    r4 = remove_words(r3)

    # Convert to Init Cap
    r5 = r4.title()

    # Strip any leading/trailing whitespace, remove any leading "-", and if the name contains any "-", strip anything after the first "-" (remove movie names)
    r6 = r5.strip().lstrip('-').split("-")[0].strip()

    # Fix spellings of commonly mis-spelled words
    result = map_title(r6,titleMappings)

    '''
    print("----------------------")
    print(title)
    print(f"Translate {r1}")
    print(f"Standardize Short {r2}")
    print(f"Remove Brackets {r3}")
    print(f"Remove Words {r4}")
    print(f"Title {r5}")
    print(f"Strip {r6}")
    print(f"Fix Spellings {result}")
    '''

    return result

def remove_brackets_spaces(title):
    # First, replace double parentheses or brackets with single ones
    result = title.replace('[[','').replace(']]','').replace('{{','').replace('}}','').replace('((','').replace('))','')
    # Next, remove any words enclosed in parentheses or brackets
    result = re.sub('\<.*?\>','',re.sub('\{.*?\}','',re.sub('\[.*?\]','',re.sub('\(.*?\)','',result))))
    # Next, collapse multiple spaces into single space
    result = re.sub('  *',' ',re.sub('\t+',' ',result))

    # If [Short] is anywhere in the name, remove it and add it to the end of the title
    if "`SHORT`" in result:
        result = (result.replace("`SHORT`","").strip() + " [SHORT]")

    return result

def remove_words(title):
    # Define lsit of words to remove and then loop through and remove them
    words = [\
        'HDR','HD','🇭 🇩','H D','ABC -','STUDIOQUALITY','HQTRACK!!','HQT','HQ','H Q','PIANO UNPLUGGED EXCLUSIVE','LOWER SCALE','AJU_STRINGS','D MAJOR',\
        'JEX','FULL SONG-','QSQT',' OST','VERSION','UNPLUGGED','DJ','LOW SCALE','REPRISE','CLEAN FIX','DUET','100%','FULL&HIGH','ORIG SCALE','FULL','ACOUSTIC',\
        'HINDI SONG','CLEAR','COVER','TRACK','ORIGINAL MUSIC','ZEHREELA INSAAN','""',' _','_1','_2','REMIX','SMC','+LIRIK','1972','HD - DUET -',\
        'NAYA DAUR','MAJOR SAAB','AASHIQUI 2','UNPLUGEG','JAB TAK HAI JAN','ARIJIT SINGH','LOVERATRI','KISHORE KUMAR','ORIGINAL','BEST',\
        'FIX','SANAM FT SANAH MOIDUTTY','BHAI BHAI','MUKESH','LATA','RAFI','JAGJIT SINGH','MUKESH','HEMANT KUMAR','HEMANT','KARAOKE','DSJ',\
        'UDIT NARAYAN','ALKA YAGNIK','SONU NIGAM','KEDARNATH','NEW-','NEW -','CUSTOMIZED','TM','RHTDM','CLP -','YESUDAS', 'LATA MANGESHKAR',\
        'FEMALE VERSION -','2502-','HD ORIG SCALE 2 -','623-','2376-', 'CAPPELLA -'\
        ]
    sorted_words = sorted(words,reverse=True,key=len)
    result = title
    for word in sorted_words:
        result = result.replace(word,'')

    # Remove any leading HH
    result = re.sub('^HH','',result)

    # Finally, clean up the witespace
    result = re.sub('[\t ]+',' ',result)
    return result

def standardize_short(title,openquote='[',closequote=']'):
    result = title.\
                replace('`SHORT`','[SHORT]').\
                replace('(SHORT HQ)','[SHORT]').\
                replace('(SHORT-HD)','[SHORT]').\
                replace('SHORT HQ)','[SHORT]').\
                replace('*SHORT*','[SHORT]').\
                replace('(SHORT HD)','[SHORT]').\
                replace('-SHORT','[SHORT]').\
                replace('SHORT-','[SHORT]').\
                replace('`SHORT`','[SHORT]').\
                replace('S H O R T','[SHORT]').\
                replace('S̶h̶o̶r̶t̶','[SHORT]').\
                replace('S̶H̶O̶R̶T̶','[SHORT]').\
                replace('[SSSF-SHORT]','[SHORT]').\
                replace('SHORTNSWEET','[SHORT]').\
                replace('{{SHORT}}','[SHORT]').\
                replace('{SHORT}','[SHORT]').\
                replace('((SHORT))','[SHORT]').\
                replace('(SHORT)','[SHORT]').\
                replace('(SHORT COVER)','[SHORT]').\
                replace('(SHORT )','[SHORT]').\
                replace('(SHORT 1)','[SHORT]').\
                replace('(SHORT & CLEAN)','[SHORT]').\
                replace('SHORT1','[SHORT]').\
                replace('SHORT_2','[SHORT]').\
                replace('SHORT_3','[SHORT]').\
                replace('SHORT','[SHORT]').\
                replace('KISHORT','KI [SHORT]').\
                replace('[[SHORT]]','[SHORT]').\
                replace('[[[[[  DHADAK  ]]]]]','DHADAK').\
                replace('SAR PAR TOPI LAL - ACCHA JI MAIN HAARI','ACCHHA JI MAIN HAARI').\
                replace('- SIMMBA',' SIMMBA').\
                replace('{HQ{','HQ ').\
                replace('6-IN-1','6 IN 1').\
                replace('JAB-JAB','JAB JAB').\
                replace('[SHORT]',openquote + 'SHORT' + closequote)

    return result

def map_title(title,titleMappings):
    # Save "Short" string if it exists in title and then remporarily remove it for the mapping logic to work correctly
    if ' [Short]' in title:
        append = ' [Short]'
    else:
        append = ''
    result = title.replace(' [Short]','')
    for fromstr,tostr in titleMappings.items():
        if result == fromstr:
            result = tostr
    # Append back the "Short" if needed
    result += append
    return result
