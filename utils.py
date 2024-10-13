import re
import random
from datetime import datetime
from .constants import *
import json, re, csv
from urllib import request

COMMENTS = {\
    'awesome':['awesome performance 👌👌👌👌👌','amazing singing 👌👌👌👌👌','awesome rendition 👌👌👌👌👌'],\
    'fantastic':['fantastic performance 👌👌👌👌','fabulous rendition 👌👌👌👌','excellent singing 👌👌👌👌'],\
    'good':['superb singing 👌👌👌','beautiful performance 👌👌👌','great rendition 👌👌👌'],\
    'average':['lovely singing 👌👌','lovely performance 👌👌','lovely rendition 👌👌'],\
    'ok':['nice rendition 👌','nicely sung 👌','nice performance 👌'],\
    'bad':['good attempt']
    }

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
def getJSON(username,type="recording",offset=0,version="legacy",sort="recent"):
    data = None
    try:
        if version == "legacy":
            urlstring = f"https://www.smule.com/{username}/{type}/json?offset={offset}"
        elif type == "following":
            urlstring = f"https://www.smule.com/api/profile/followees?accountId={username}&offset={offset}&limit=25"
        else:
            urlstring = f"https://www.smule.com/search/by_type?q={username}&type={type}&sort={sort}&offset={offset}&size=0"
        #print(urlstring)
        with request.urlopen(urlstring) as url:
            data = json.loads(url.read())
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
            'ᵇ𝓐𝓭𝓷𝓪⑥⑤④⓪ˣ𝙃𝘿⁵③⑦ⒾⒺⓘⓔʍǟⒸⓟⓙⓃ𝐮𝐥ᴜɪᴍᴋʟᴀH𝐐𝐅u𝐋𝑯𝑫ᴼαηⒼⓀⓜⒷⓑⒽⓉⒽⓌⓕⒻⓛᴄoᴠᴇrᵖᵀᴹᵈⁱᵍⁱᵗᵃˡⓏᶻᵘⓩ𝗦𝗮𝗻𝗺𝗣u𝗿𝗶𝗨𝗘𝗧ⓎⒶⓐⓨⁿⓅᵐD𝐔𝐄𝐓𝗙𝘂𝗹𝗹𝗛𝗗𝐎🆂🅷Ⓞ🆁🆃🅦ʰᴮᵉˢᵗᶜᵒᵛᵉʳＳＨＯＲＴᴅᴾᴸᴳᴱᑕᗰᑎ🅚Ⓢⓤ𝔻𝕀𝔾Sʜᴏʀᴛ🆅ⓦⓖᎥᑭƳᖇᗪ　𝑺Fϙ𝕾𝒉𝒐𝒓𝒕🅟🅔🆆🇲🇫ÅåȟȋJᒎᗷᕼᗩ𝔖𝐡𝐨𝐫𝐭ᵁᴺᵂᴵ𝐇𝐃🄷🅀🆇🅿🆉ᴿ🇶Ⓡ🅠🇪🇱🇦🇬🅖🅜🅢🅗🅞🅡🅣ⓔⓘ🅹🅵🄷🅀ⓢⓗⓞⓡⓣ🅕🅤🅛🅛ᴴᴰ🇭🇩🇸🅝🇭🇴🇷🇹🅑🅘🇼🄷🅀🇰🇦🇺🇳🅢🆈🅼🅆🅅🅓🅳🅉🄱ℍ🅀ℚ🅙🅧🅒🅗🅤🅡🅐🄷🅄🄼🅂🄰🄵🄰🅁🅂🄷🄾🅁🅃🆂🅷🅾🆁🆃🄲🄷🄰🄸🄽🄺🄳🅃🄴🄻🄶🄿🅴🅷🆀🅺🆄🅲🅷🅾🆁🅸🅶🅸🅽🅰🅻🅱ⓓⓗⓐⓓⓚⓐⓝⒹ【】🄹🅈',\
            'BADNA6540XHD537IEIEMACPJNULUIMKLAHQFULHDOANGKMBBHTHWFFLCOVERPTMDIGITALZZUZSANMPURIUETYAAYNPMDUETFULLHDOSHORTWHBESTCOVERSHORTDPLGECMNKSUDIGSHORTVWGIPYRD SFQSHORTPEWMFAAHIJJBHASHORTUNWIHDHQXPZRQRQELAGGMSHORTEIJFHQSHORTFULLHDHDSNHORTBIWHQKAUNSYMWVDDZBQHQJXCHURAHUMSAFARSHORTSHORTCHAINKDTELGPEHQKUCHORIGINALBdhadkanD[]JY',\
            '😜💍☂👧~🪔🔱🔵💅🙌♫💊👮😰⏭⏮🧶✫🌋😆⚔☾✮☆🐈🎂👠👞👡¶🤟😁🏃🔯💫🤷🍻🐞😐🛫☑📀🆑🪁🔐🆘💪😈▲💢🔝🤘〘〙🇲♧🚩🐅²👼🍒🍷📿*►🦂🦢📼⏩🍄¹🤭♣࿐😭🏠😌😥❉🦋🤝♪🔰💐³༒🌝👁😻🏇🚴🧚🎨☜🎹🎵🧡😃🌈°🏝⛱🌄💿💏🇮🇳🎶✌️👬🌾▶️◀️🖐✊😋✅🎊🎆🌴🐧♾️😢😪🖤💌🙃💓🙇‍♀️🌺​⏏️☞📌🎭🐎☺️★👱🙅‍♂️🕊+🌧⛈🌨🇦🇼🇦🇨🕸👩‍❤️‍👨❣️🔊😉💯👸😎🌃📚😊👩🏻🤗⚡‍💼🎀❌❤💛🥀😗👍🎻✿●•🎞💦🇨🇻🌖💎🌜⭐🌛👩✨😙💔–@🙏☛☚▫💋🏼‍♂♀👌!.❄🎷🗿👫🔘💥🎙©🆕️☄🚶🚶🤔🥰🎸🕺👈🎼😘/”“🦁⚜️🕉️⏯️🌙"|💚💖🌸🌻🤪👉💜🐝🍀✔💕💝♥🌹☔🌧️🌩️🌦️🙈™💑®@🎧📝🌷🍁🍂🍃🌼💗👀🤫👑💑🌟🎤💙⚘🙄❤#💗™💘🤹😍💟💞🔥😇🤩😏Ⱥ💃🎈=😔'\
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
        'JEX','QSQT',' OST','VERSION','UNPLUGGED','DJ','LOW SCALE','REPRISE','CLEAN FIX','DUET','100%','FULL&HIGH','ORIG SCALE','FULL','ACOUSTIC',\
        'HINDI SONG','CLEAR','COVER','TRACK','ORIGINAL MUSIC','ZEHREELA INSAAN','""',' _','_1','_2','REMIX','SMC','+LIRIK','1972','HD - DUET -',\
        'NAYA DAUR','MAJOR SAAB','AASHIQUI 2','UNPLUGEG','JAB TAK HAI JAN','ARIJIT SINGH','LOVERATRI','KISHORE KUMAR','ORIGINAL','BEST',\
        'FIX','SANAM FT SANAH MOIDUTTY','BHAI BHAI','MUKESH','LATA','RAFI','JAGJIT SINGH','MUKESH','HEMANT KUMAR','HEMANT','KARAOKE','DSJ',\
        'UDIT NARAYAN','ALKA YAGNIK','SONU NIGAM','KEDARNATH','NEW-','NEW -','CUSTOMIZED','TM','RHTDM','CLP -','YESUDAS', 'LATA MANGESHKAR',\
        'FEMALE VERSION -'\
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
