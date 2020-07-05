import re
from .models import db

# The title field we get from Smule for performances contains many letters and words that are not appropriate for the filename
# Fix the title to remove/replace these so that we can use this "fixed" title in the filename
def fix_title(title,titleMappings):
    # Define translation table to translate all graphical letters to actual letters, and strip out all the symbols
    ttable = title.maketrans(\
            '𝐇𝐃🄷🅀🆇🅿🆉ᴿ🇶Ⓡ🅠🇪🇱🇦🇬🅖🅜🅢🅗🅞🅡🅣ⓔⓘ🅹🅵🄷🅀ⓢⓗⓞⓡⓣ🅕🅤🅛🅛ᴴᴰ🇭🇩🇸🅝🇭🇴🇷🇹🅑🅘🇼🄷🅀🇰🇦🇺🇳🅢🆈🅼🅆🅅🅓🅳🅉🄱ℍ🅀ℚ🅙🅧🅒🅗🅤🅡🅐🄷🅄🄼🅂🄰🄵🄰🅁🅂🄷🄾🅁🅃🆂🅷🅾🆁🆃🄲🄷🄰🄸🄽🄺🄳🅃🄴🄻🄶🄿🅴🅷🆀🅺🆄🅲🅷🅾🆁🅸🅶🅸🅽🅰🅻🅱ⓓⓗⓐⓓⓚⓐⓝⒹ【】🄹🅈',\
            'HDHQXPZRQRQELAGGMSHORTEIJFHQSHORTFULLHDHDSNHORTBIWHQKAUNSYMWVDDZBQHQJXCHURAHUMSAFARSHORTSHORTCHAINKDTELGPEHQKUCHORIGINALBdhadkanD[]JY',\
            '♾️😢😪🖤💌🙃💓🙇‍♀️🌺​ᵈⁱᵍⁱᵗᵃˡ⏏️☞📌🎭🐎☺️ᵀᴹ★👱🙅‍♂️🕊+🌧⛈🌨🇦🇼🇦🇨🕸👩‍❤️‍👨❣️🔊😉💯👸😎🌃📚😊👩🏻🤗⚡‍💼🎀❌❤💛🥀😗👍🎻✿●•🎞💦🇨🇻🌖💎🌜⭐🌛👩✨😙💔–@🙏☛☚▫💋🏼‍♂♀👌!.❄🎷🗿👫🔘💥🎙©🆕️☄🚶🚶🤔🥰🎸🕺👈🎼😘/”“🦁⚜️🕉️⏯️🌙"|💚💖🌸🌻🤪👉💜🐝🍀✔💕💝♥🌹☔🌧️🌩️🌦️🙈™💑®@🎧📝🌷🍁🍂🍃🌼💗👀🤫👑💑🌟🎤💙⚘🙄❤#💗™💘🤹😍💟💞🔥😇🤩😏Ⱥ💃🎈=😔'\
            )

    # Do the translation and convert to uppercase temporarily
    r1 = title.translate(ttable).upper()

    # Standardize all versions of "short" to "`Short`"
    r2 = standardize_short(r1,'`','`')

    # Remove brackets
    r3 = remove_brackets(r2)

    # Remove unnecessary words
    r4 = remove_words(r3)

    # Convert to Init Cap
    r5 = r4.title()

    # Strip any leading/trailing whitespace, remove any leading "-", and if the name contains any "-", strip anything after the first "-" (remove movie names)
    r6 = r5.strip().lstrip('-').split("-")[0].strip()

    # Fix spellings of commonly mis-spelled words
    result = map_titles(r6,titleMappings)

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

def remove_brackets(title):
    # First, replace double parentheses or brackets with single ones
    result = title.replace('[[','').replace(']]','').replace('{{','').replace('}}','').replace('((','').replace('))','')
    # Next, remove any words enclosed in parentheses or brackets
    result = re.sub('\<.*?\>','',re.sub('\{.*?\}','',re.sub('\[.*?\]','',re.sub('\(.*?\)','',result))))

    # If [Short] is anywhere in the name, remove it and add it to the end of the title
    if "`SHORT`" in result:
        result = (result.replace("`SHORT`","").strip() + " [SHORT]")

    return result

def remove_words(title):
    # Define lsit of words to remove and then loop through and remove them
    words = [\
        'HDR','HD','H D','ABC -','STUDIOQUALITY','HQTRACK!!','HQT','HQ','H Q','PIANO UNPLUGGED EXCLUSIVE','LOWER SCALE','AJU_STRINGS','D MAJOR',\
        'JEX','QSQT',' OST','VERSION','UNPLUGGED','DJ','LOW SCALE','REPRISE','MASHUP','CLEAN FIX','DUET','100%','FULL&HIGH','FULL',\
        'HINDI SONG','CLEAR','COVER','TRACK','ORIGINAL MUSIC','ZEHREELA INSAAN','""',' _','_1','_2','REMIX','SMC','+LIRIK','1972',\
        'NAYA DAUR','MAJOR SAAB','AASHIQUI 2','UNPLUGEG','JAB TAK HAI JAN','ARIJIT SINGH','LOVERATRI','KISHORE KUMAR','ORIGINAL','BEST',\
        'FIX','SANAM FT SANAH MOIDUTTY','BHAI BHAI','FIZA','AIRLIFT','MUKESH','LATA','RAFI','JAGJIT SINGH','MUKESH','HEMANT KUMAR','HEMANT','KARAOKE','DSJ',\
        'UDIT NARAYAN','ALKA YAGNIK','SONU NIGAM'\
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
                replace('(SHORT-HD)','[SHORT]').\
                replace('SHORT HQ)','[SHORT]').\
                replace('*SHORT*','[SHORT]').\
                replace('(SHORT HD)','[SHORT]').\
                replace('-SHORT','[SHORT]').\
                replace('SHORT-','[SHORT]').\
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
                replace('[SHORT]',openquote + 'SHORT' + closequote)
    return result

def map_titles(title,titleMappings):
    # Save "Short" string if it exists in title and then remporarily remove it for the mapping logic to work correctly
    if ' [Short]' in title:
        append = ' [Short]'
    else:
        append = ''
    result = title.replace(' [Short]','')
    #d = spelling_dict()
    #d = fetchTitleMappings()
    for fromstr,tostr in titleMappings.items():
        if result == fromstr:
            result = tostr
        #result = result.replace(fromstr,tostr)
    # Append back the "Short" if needed
    result += append
    return result

def spelling_dict():
    d = {\
            "Aajkal ": "Aaj Kal ",\
            "Lagja ": "Lag Ja ",\
            "Mai ": "Main ",\
            "Aapki ": "Aap Ki ",\
            "Aapka ": "Aap Ka ",\
            "Jane ": "Jaane ",\
            "Diwana ": "Deewana ",\
            "Kahan ": "Kaha ",\
            "Jadu ": "Jaadu ",\
            "Wo ": "Woh ",\
            "Awaz ": "Awaaz ",\
            "Aawaz ": "Awaaz ",\
            "Abc ": "Chahun Mai Ya Na ",\
            "Ad ": "",\
            "Adpyar ": "Pyar",\
            "Toh ": "To ",\
            "Ankho ": "Ankhon ",\
            "Janeman": "Jaaneman",\
            "Ayeae ": "Ae ",\
            "Aye Ho": "Aaye Ho",\
            "Aye ": "Ae ",\
            "Babu Ji ": "Babuji ",\
            "Chahu ": "Chanun ",\
            "Chhu Kar": "Chhookar",\
            "Jao Chor Kar": "Jao Chhod Kar",\
            "Chhukarmere": "Chhookar Mere",\
            "Chhukar": "Chhookar",\
            "Cu ": "Chhu ",\
            "Cukar": "Chhookar",\
            "Chod Do": "Chhod Do",\
            "Cod Do": "Chhod Do",\
            "Chookar": "Chhookar",\
            "Chorichori": "Chori Chori",\
            "Chu Kar": "Chhookar",\
            "Churaake": "Chura Ke",\
            "Churakedil": "Chura Ke Dil",\
            "Hiaana": "Hi Aana",\
            "Hum Ko": "Humko",\
            "Humkohumise": "Humko Hamise",\
            "Kauntujhe": "Kaun Tujhe",\
            "Rooptera": "Roop Tera",\
            "(Pure) Uthe Sab Ke Kadam": "Uthe Sab Ke Kadam",\
            "Aa Bhi Jaa Aa Jaa": "Aa Bhi Jaa",\
            "Aa Bhi Jaa Aa Bhi Jaa": "Aa Bhi Jaa",\
            "Aa Bhi Jaa Aa Bhi Ja": "Aa Bhi Jaa",\
            "Aa Bhi Ja Aa Bhi Ja": "Aa Bhi Jaa",\
            "Aa Bhi Ja ": "Aa Bhi Jaa ",\
            "Aaj Kal Tere Mere Pyaar Ke Charche": "Aaj Kal Tere Mere",\
            "Aaj Kal Tere Mere Pyar Ke Charche": "Aaj Kal Tere Mere",\
            "Aaj Kal Tere Mere Pyar": "Aaj Kal Tere Mere",\
            "Aaj Mein Upar Aasmaan Niche": "Aaj Main Upar",\
            "Aaja Sanam Madhur Chandni Me Hum": "Aaja Sanam Madhur",\
            "Aaja Sanam Madhur Chandni Mein Ham": "Aaja Sanam Madhur",\
            "Aaja Sanam Madhur New Clean": "Aaja Sanam Madhur",\
            "Aajkalteremereaw Pyarkecharche": "Aaj Kal Tere Mere",\
            "Aajkalteremereawpyarkecharche": "Aaj Kal Tere Mere",\
            "Aajkalteremerepyarkecharche": "Aaj Kal Tere Mere Pyaar Ke Charche ",\
            "Aanewala Pal Janewala Hai": "Aane Wala Pal",\
            "Aankhon Hi Aakhhon Mein Ishara": "Aankhon Hi Aankhon Mein Ishara",\
            "Aap Ka Aana Dil Dhar Kana": "Aap Ka Aana Dil Dhadkana",\
            "Aap Ki Aakhon Main Kuch": "Aap Ki Aankho",\
            "Aap Ki Aakhon Main": "Aap Ki Aankho",\
            "Aap Ki Aankho Kuch": "Aap Ki Aankho",\
            "Aap Ki Ankhon Mein Kuch": "Aap Ki Aankho",\
            "Aaye Ho Mere Jindagi Me": "Aaye Ho Meri Zindagi Mein",\
            "Accha Ji Main Haari Hq": "Accha Ji Main Haari",\
            "Accha To Hum Chalte Hai": "Achha To Hum Chalte Hain",\
            "Acha To Hum Chalte Hai Accha Toh": "Achha To Hum Chalte Hain",\
            "Acha To Hum": "Achha To Hum Chalte Hain",\
            "Achha Ji Main Haari Chalo": "Accha Ji Main Haari",\
            "Achha To Hum Chalte Hain Chalte Hai Accha Toh": "Achha To Hum Chalte Hain",\
            "Achhha Ji Mein Hari": "Accha Ji Main Haari",\
            "Ae Ajnabee Tu Bhi Kabhi": "Ae Ajnabi",\
            "Ae Ajnabi Awaaz De Kahin Se": "Ae Ajnabi",\
            "Ae Ajnabi Tu Bhi Kabhi Awaaz De Kahin Se": "Ae Ajnabi",\
            "Ae Ajnabi Tu Bhi Kabhi": "Ae Ajnabi",\
            "Ae Dil Laya Hai Bahaar Kya Kehna": "Ae Dil Laya Hai Bahaar",\
            "Ae Dil Laya Hai, Kya Kehna": "Ae Dil Laya Hai Bahaar",\
            "Ae Mere Humsafar Aye": "Ae Mere Humsafar",\
            "Ae Mere Zohra Zabeen": "Ae Meri Zohra Zabeen",\
            "Ae Meri Johra Jabee": "Ae Meri Zohra Zabeen",\
            "Ae Meri Zohara Zabeen": "Ae Meri Zohra Zabeen",\
            "Agar Tum Saath Ho Hd": "Agar Tum Saath Ho",\
            "Agar Tum Saath Ho Tamasha": "Agar Tum Saath Ho",\
            "Airlift ( Tenu Itna Me Pyar Karan)": "Tenu Itna Me Pyar Karan",\
            "Aji Roothkar Ab": "Aji Roothkar",\
            "Ajnabi Mujhko Itna Bata Hita": "Ajnabi Mujhko Itna Bata",\
            "Ajnabi Mujko Itna Bata": "Ajnabi Mujhko Itna Bata",\
            "Ankhon Hi Ankhon Mein": "Aankhon Hi Aankhon Mein Ishara",\
            "Ankhon Se Tune Ye Kya": "Ankhon Se Tune Ye",\
            "Are Re Are Ye Kya Hua": "Are Re Are",\
            "Awaaz Do Hamko": "Awaaz Do Humko",\
            "Awaaz Do Humko  Hq": "Awaaz Do Humko",\
            "Awaaz Do Humko ( )": "Awaaz Do Humko",\
            "Awaaz Do Humko ( Hd)": "Awaaz Do Humko",\
            "Awaaz Do Humko ()": "Awaaz Do Humko",\
            "Awaaz Do Humko A": "Awaaz Do Humko",\
            "Awaaz Do Humko Dushman": "Awaaz Do Humko",\
            "Awaaz Do Humko Hum Kho Gaye": "Awaaz Do Humko",\
            "AwaazDo Hamko": "Awaaz Do Humko",\
            "AwaazDo Humko Dushman": "Awaaz Do Humko",\
            "AwaazDo Humko": "Awaaz Do Humko",\
            "Baahon Ke Darmiyan": "Baahon Ke Darmiyaan",\
            "Babuji Dheere Chalna (Aar Paar)": "Babuji Dheere Chalna",\
            "Bahon Ke Darmiyan": "Baahon Ke Darmiyaan",\
            "Bahonke Darmiyan Khamoshi Movie": "Baahon Ke Darmiyaan",\
            "Bahut Pyar Karte Hai Tumko Sanam": "Bahut Pyar Karte Hain",\
            "Bahut Pyar Karte Hai": "Bahut Pyar Karte Hain",\
            "Bahut Pyar Karte Hain Tumko Sanam": "Bahut Pyar Karte Hain",\
            "Bahut Pyar Karte Hainn": "Bahut Pyar Karte Hain",\
            "Best Dum Bhar Jo Udhar": "Dum Bhar Jo Udhar",\
            "Bholi Si Surat Re": "Bholi Si Surat",\
            "Bindiya Chamkegi U": "Bindiya Chamkegi",\
            "Bindiya Chamkegihd": "Bindiya Chamkegi",\
            "Can'T Help Falling In Love": "Can't Help Falling In Love",\
            "Chahun Main Ya Naa": "Chahun Main Ya Na",\
            "Chal Jhoothi Hq": "Chal Jhoothi",\
            "Chalte Chalte Yunhi": "Chalte Chalte",\
            "Chand Ne Kuch Kahahq": "Chand Ne Kuch Kaha",\
            "Chand Ne Kuchh Kaha": "Chand Ne Kuch Kaha",\
            "Chanun Main Ya Na Aashiqui2": "Chahun Main Ya Na",\
            "Chaudavi Ka Chaand Ho": "Chaudhvin Ka Chand Ho",\
            "Chaudavi Ka Chand Ho": "Chaudhvin Ka Chand Ho",\
            "Chaudhvin Ka Chand Ho Hq": "Chaudhvin Ka Chand Ho",\
            "Chhod Do Aanchal Kya Kahega": "Chhod Do Aanchal",\
            "Chhod Do Aanchal Zamana Kya Kahega": "Chhod Do Aanchal",\
            "Chhod Do Aanchal Zamana": "Chhod Do Aanchal",\
            "Chhookar Mere Maan Ko": "Chhookar Mere Man Ko",\
            "Chhookar Mere Man Ko  Kar": "Chhookar Mere Man Ko",\
            "Chhookar Mere Manko": "Chhookar Mere Man Ko",\
            "Chhookar Mere Mann": "Chhookar Mere Man Ko",\
            "Chhup Gaya Badli Mein Jaake Chand Bhi Sharma": "Chhup Gaya Badli Mein Jaake Chand",\
            "Chogada Tara–": "Chogada Tara",\
            "Chori Chori Jab Nazarein Mili": "Chori Chori Jab Nazrein Mili",\
            "Chori Chori Jab Nazaren": "Chori Chori Jab Nazrein Mili",\
            "Chori Chori Jab Nazre Mili": "Chori Chori Jab Nazrein Mili",\
            "Chori Chori Jab Nazrein Mili  Hq": "Chori Chori Jab Nazrein Mili",\
            "Chori Chori Jabnazrein Kareeb": "Chori Chori Jab Nazrein Mili",\
            "Chura Ke Dil Mera Goriya Chali": "Chura Ke Dil Mera",\
            "Chura Lia Hai": "Chura Liya Hai",\
            "Chura Liya Hai Tumne Jo Dil Ko": "Chura Liya Hai",\
            "Chura Lo Na Dil Mera Kareeb": "Chura Lo Na Dil Mera Sanam",\
            "Churake Dil Mera": "Chura Ke Dil Mera",\
            "Dagabaaz Re Dabangg 2": "Dagabaaz Re",\
            "Deewana Hua Badal  Pallavi": "Deewana Hua Badal",\
            "Deewana Hua Badal Hq": "Deewana Hua Badal",\
            "Dekha Ek Khwaab To Ye Silsile": "Dekha Ek Khwaab To Yeh Silsile",\
            "Dekha Ek Khwaab To Yeh Silsile Hue": "Dekha Ek Khwaab To Yeh Silsile",\
            "Dekha Ek Khwaab To Yeh Silsilet": "Dekha Ek Khwaab To Yeh Silsile",\
            "Dekha Ek Khwab": "Dekha Ek Khwaab To Yeh Silsile",\
            "Dekho Maine Dekha Hai Sapna": "Dekho Maine Dekha Hai",\
            "Dekho Maine Dekha Hai Ye Ik Sapna": "Dekho Maine Dekha Hai",\
            "Dekho Maine Dekha Hai Ye Ik": "Dekho Maine Dekha Hai",\
            "Dheere Dheere Chal Chaand Gagan Mein": "Dheere Dheere Chal Chand Gagan Mein",\
            "Dheeredheer Se Dheere": "Dheere Dheere Se",\
            "Dil Hai Tumhara  Hindi Song": "Dil Hai Tumhara",\
            "Dil Hai Tumhara Dil Hai": "Dil Hai Tumhara",\
            "Dil Ka Bhanwar Kare Pukar ,Tere Ghar Ke Samne": "Dil Ka Bhanwar Kare Pukar",\
            "Dil Ke Armaan Aansuon Mein Beh Gaye": "Dil Ke Armaan",\
            "Dil Ke Arman Aansuon Mein Beh Gaye": "Dil Ke Armaan",\
            "Dil Ke Arman": "Dil Ke Armaan",\
            "Dil Ke Jharokhe Mein Tujhko Bithakar": "Dil Ke Jharoke Mein Tujhko Bithakar",\
            "Dil Kya Kare Jab Kisi Se": "Dil Kya Kare Jab Kisi Ko",\
            "Dil Leke Dard ": "Dil Leke Darde Dil ",\
            "Dil Leke Dard E Dil": "Dil Leke Darde Dil",\
            "Dil Leke Darde Dil E Dil": "Dil Leke Darde Dil",\
            "Dil Leke Darde Dile Dil": "Dil Leke Darde Dil",\
            "Dil Ne Yeh Kaha Hai Dil Se": "Dil Ne Yeh Kaha Hai",\
            "Dil Tadap Tadap Ket": "Dil Tadap Tadap Ke",\
            "Dodilmilrahe Hain": "Do Dil Mil Rahe Hai",\
            "Do Dil Mil Rahe Hai (&High Quality)": "Do Dil Mil Rahe Hai",\
            "Do Dil Mil Rahe Hai Female": "Do Dil Mil Rahe Hai",\
            "Do Dil Mil Rahe Hain (&High Quality)": "Do Dil Mil Rahe Hai",\
            "Do Dil Mil Rahe Hain Female": "Do Dil Mil Rahe Hai",\
            "Do Dil Mil Rahe Hain": "Do Dil Mil Rahe Hai",\
            "Do Lafzon Ki Hai Asha Bhosle": "Do Lafzon Ki Hai",\
            "Do Pal Ruka (Veer": "Do Pal Ruka",\
            "Do Pal Ruka Khwabon Ka Do Pal Ruka Pal Ruka": "Do Pal Ruka",\
            "Do Pal Ruka Khwabon Ka Karwan": "Do Pal Ruka",\
            "Do Pal Ruka Khwabon Ka Original Do Pal Ruka": "Do Pal Ruka",\
            "Do Pal Ruka Pal Ruka": "Do Pal Ruka",\
            "E Ajnabi (Dil Se) Clean": "Ae Ajnabi",\
            "Ehsaantera Hoga Mujh Par": "Ehsaan Tera Hoga Mujh Par",\
            "Ehsan Tera Hoga Mujh Par": "Ehsaan Tera Hoga Mujh Par",\
            "Ek Ladki Ko Dekhahd": "Ek Ladki Ko Dekha",\
            "Ek Pyaar Ka Nagma Hai Shor 1972": "Ek Pyar Ka Nagma Hai",\
            "Ek Pyaar Kaa Nagmaa Hai": "Ek Pyar Ka Nagma Hai",\
            "Ek Pyar Ka Nagma Hai Nagma": "Ek Pyar Ka Nagma Hai",\
            "Ek Pyar Ka Nagma Hai(Shor)": "Ek Pyar Ka Nagma Hai [Short]",\
            "Ek Pyar Ka Pyar Ka": "Ek Pyar Ka Nagma Hai",\
            "Ekpyar Ka [Short]": "Ek Pyar Ka Nagma Hai [Short]",\
            "Ekpyarkanagma": "Ek Pyar Ka Nagma Hai",\
            "Eshaan Tera Hoga Mujh Par": "Ehsaan Tera Hoga Mujh Par",\
            "F Tujh Mein Rab Dikhta Hai Female": "Tujh Mein Rab Dikhta Hai",\
            "Female Moh Moh Ke Dhaage": "Moh Moh Ke Dhaage",\
            "Fix Aap Ki Aankho Kuch": "Aap Ki Aankho",\
            "Fix Aap Ki Ankhon Mein Kuch": "Aap Ki Ankhon Mein Kuch",\
            "Gazab Ka Hai Din Qayamat Se Qayamat Tak": "Gazab Ka Hai Din",\
            "Ghar Se Nikalte Hi Kuchh Dur Chalte Hi": "Ghar Se Nikalte Hi",\
            "Gulabi Ankhe Jo Teri Dekhi": "Gulabi Aankhen",\
            "Gulabi Ankhen": "Gulabi Aankhen",\
            "Gun Guna Rahe Hai Bhanware (Aaradhna)": "Gunguna Rahe Hain Bhanwre",\
            "Gunguna Rahe Hain Bhanwre Aradhana": "Gunguna Rahe Hain Bhanwre",\
            "Haal Kaisa Hai Janaab Ka": "Haal Kaisa Hai",\
            "Haal Kaisa Hai Janab Ka": "Haal Kaisa Hai",\
            "Hai Mera Dil Josh ( Original)": "Hai Mera Dil",\
            "Hai Rama Ye Kya Hua Rangeela": "Hai Rama Ye Kya Hua",\
            "Hame Tumse Pyar Kitna ( )": "Hamein Tumse Pyar Kitna",\
            "Hame Tumse Pyar Kitna": "Hamein Tumse Pyar Kitna",\
            "Hamein Tumse Pyar Kitna ( Piano)": "Hamein Tumse Pyar Kitna",\
            "Hangover  Kick": "Hangover",\
            "Har Ghadi Badal Rahi Hai": "Har Ghadi",\
            "Har Ghadi Badal Rahi": "Har Ghadi",\
            "Har Ghadi Hai": "Har Ghadi",\
            "Har Ghadi Hait": "Har Ghadi",\
            "Haye Mera Dil Churake Le Gaya": "Hai Mera Dil",\
            "Hd Ankhon Se Tune Ye": "Aankhon Se Tune Ye",\
            "Hd Chori Chori Jab Nazrein Mili": "Chori Chori Jab Nazrein Mili",\
            "Hd Tere Liye": "Tere Liye",\
            "Hdchookar Mere Mann": "Chhookar Mere Man Ko",\
            "Hdmain Agar Kahoon": "Main Agar Kahoon",\
            "Hdmain Pal Do Pal Ka": "Main Pal Do Pal Ka",\
            "Hdtu Mile Dil Dil": "Tu Mile Dil Dil",\
            "Hh Kaun Tujhe": "Kaun Tujhe",\
            "Hh Suhani Raat Dhal Chuki": "Suhani Raat Dhal Chuki",\
            "Hhsocha Hai": "Socha Hai",\
            "Hhtum Dil Ki Dhadkan Mein": "Tum Dil Ki Dhadkan Mein",\
            "Hil Hai Ki Manta Nahi": "Dil Hai Ki Manta Nahi",\
            "Honthon Se Chu Lo Tum": "Hothon Se Chhu Lo Tum",\
            "Hoton Se Chhulo Tum": "Hothon Se Chhu Lo Tum",\
            "Hum Ko Humise Chura Lo Humise Humise": "Hum Ko Humise Chura Lo",\
            "Hume Tumse Pyaar Kitna Hume": "Humein Tumse Pyaar",\
            "Hume Tumse Pyaar Kitna Recreation": "Humein Tumse Pyaar",\
            "Hume Tumse Pyaar Kitna": "Humein Tumse Pyaar",\
            "Hume Tumse Pyaar": "Humein Tumse Pyaar",\
            "Humein Tumse Pyaar Kitna Hume": "Humein Tumse Pyaar Kitna",\
            "Humein Tumse Pyaar Kitna Kitna Hume": "Humein Tumse Pyaar Kitna",\
            "Humein Tumse Pyaar Kitna Kitna Recreation": "Humein Tumse Pyaar Kitna",\
            "Humein Tumse Pyaar Kitna Kitna": "Humein Tumse Pyaar Kitna",\
            "Humein Tumse Pyaar Kitna Recreation": "Humein Tumse Pyaar Kitna",\
            "Humko Humise Chura Lo Humise Humise": "Humko Humise Chura Lo",\
            "Humko Humise Chura Lo": "Humko Humise Chura Lo",\
            "Humko Humise Churalo": "Humko Humise Chura Lo",\
            "Humkohumise Chura Chura": "Humko Humise Chura Lo",\
            "Humyaar Hai Tumhare": "Hum Yaar Hai Tumhare",\
            "Is Bina (Taal)": "Ishq Bina",\
            "Is Shava": "Ishq Shava",\
            "Isbina (Taal)": "Ishq Bina",\
            "Isshava": "Ishq Shava",\
            "Isharon Isharon Mein Isharon Mein": "Isharon Isharon Mein",\
            "Itna Na Mujhse To Pyarr Badha": "Itna Na Mujhse Tu Pyar Badha",\
            "Jaadu Hai Ns": "Jaadu Hai Nasha Hai",\
            "Jaane Chaman Shola Jane": "Jaane Chaman Shola Badan",\
            "Jaane Jaan Dhoondta Phir Raha": "Jaane Jaan Dhoondta",\
            "Jaane Jaan Dhoondta Phir": "Jaane Jaan Dhoondta",\
            "Jaane Jaan Dhoondta Raha": "Jaane Jaan Dhoondta",\
            "Jaane Kaise Kab Iqraar Ho Gaya (Shakti)": "Jaane Kaise Kab",\
            "Jaane Kaise Kab Kahan Iqraar Ho Gaya (Shakti)": "Jaane Kaise Kab",\
            "Jaane Kaise Kab Kahan": "Jaane Kaise Kab",\
            "Jaane Kyon Log Pyaar": "Jaane Kyun Log Pyar",\
            "Jab Koi Baat Bigad Jaaye": "Jab Koi Baat",\
            "Jab Koi Baat Bigad": "Jab Koi Baat",\
            "Jab Koi Baat Jaaye": "Jab Koi Baat",\
            "Jab Se Tere Naina  Saawariya": "Jab Se Tere Naina",\
            "Jab Se Tere Naina ( )": "Jab Se Tere Naina",\
            "Jadoo Hai Nasha Hai": "Jadu Hai Nasha Hai",\
            "Janam Dekhlo Mit ( )": "Janam Dekhlo Mit",\
            "Janam Dekhlo Mit ()": "Jaanam Dekh Lo",\
            "Jane Kahan Gaye Woh Dinhd": "Jane Kahan Gaye Woh Din",\
            "Jane Kyu Log Pyar Karte Hain": "Jaane Kyun Log Pyar",\
            "Jawani Jaaneman Haseen Dilrubaeman Haseen Dilruba (Namak Halaal)": "Jawani Jaaneman Haseen Dilruba",\
            "Jawani Janeman Haseen Dilruba (Namak Halaal)": "Jawani Jaaneman Haseen Dilruba",\
            "Jawani Jan": "Jawani Jaaneman Haseen Dilruba",\
            "Jhilamil Sitaaro Kaa Angan Hoga": "Jhilmil Sitaron Ka",\
            "Jhilmil Sitaron Ka Aangan": "Jhilmil Sitaron Ka",\
            "Jhilmil Sitaron Ka Angan": "Jhilmil Sitaron Ka",\
            "Jhuki Jhuki Si Nazart": "Jhuki Jhuki Si Nazar",\
            "Kabhi Kabhi Meint": "Kabhi Kabhi",\
            "Kabhi Kabhi Mein": "Kabhi Kabhi",\
            "Kabhi Kabhi Mere Dil Mein": "Kabhi Kabhi",\
            "Kabhi Kabhi Mere Dil": "Kabhi Kabhi",\
            "Kabhikabhi": "Kabhi Kabhi",\
            "Kabira Encore": "Kabira",\
            "Kaho Na Pyaar Hai U": "Kaho Na Pyaar Hai",\
            "Kaho Na Pyaar Haihd": "Kaho Na Pyaar Hai",\
            "Kaun Tujhe Ms Dhoni The Untold Story": "Kaun Tujhe",\
            "Kaun Tujhe Ms Dhoni": "Kaun Tujhe",\
            "Kaun Tujhe The Untold Story": "Kaun Tujhe",\
            "Kaun Tujhe Tujhe": "Kaun Tujhe",\
            "Kaun Tujhe Yun Peyar Karego": "Kaun Tujhe",\
            "Kaun Tujhe {Piano }": "Kaun Tujhe",\
            "Kehta Hai Pal Pal Tumse": "Kehta Hai Pal Pal",\
            "Key Sera Sera": "Ke Sera Sera",\
            "Kitna Pyara Waada Hai": "Kitna Pyara Waada",\
            "Koi Hero Yahan, Koi Zero Yahan I Am The Best": "I Am The Best",\
            "Koi Ladki Hai Original Music": "Koi Ladki Hai",\
            "Kuch Kuch Hota Haihota Hai Ori": "Kuch Kuch Hota Hai",\
            "Kuchh Na Kaho": "Kuch Na Kaho",\
            "Kuch Kuch Hota Hai Ori": "Kuch Kuch Hota Hai",\
            "Kya Yehi Pyaar Hai": "Kya Yahi Pyar Hai",\
            "Kyun Main Jaagoon Low Scale": "Kyun Main Jaagoon Low Scale",\
            "Lag Ja Galeja Gale Ja Gale": "Lag Ja Gale",\
            "Lag Ja Galeoriginal Lag Ja": "Lag Ja Gale",\
            "Lamha Lamha Doori Gangster": "Lamha Lamha Doori",\
            "Likhe Jo Khat Tujhe Jo Khat Tujhe": "Likhe Jo Khat Tujhe",\
            "Maang Ke Saath Tumhara:": "Maang Ke Saath Tumhara",\
            "Main Agar Kahoon ( )": "Main Agar Kahoon",\
            "Main Hoon Na ( )": "Main Hoon Na",\
            "Main Koi Aisa Geet Gaoon": "Main Koi Aisa Geet",\
            "Mana Janab Ne Pukara Nahin": "Mana Janab Ne Pukara Nahi",\
            "Mashup Kaun Tujhe Ms Dhoni": "Kaun Tujhe",\
            "Mashup Kaun Tujhe": "Kaun Tujhe",\
            "Mein Tenu Samjhao": "Main Tenu Samjhawan Ki",\
            "Mera Joota Hai Jaapani": "Mera Joota Hai Japani",\
            "Mera Naam Chin Chin Chu ( & Timing)": "Mera Naam Chin Chin Chu",\
            "Mera Naam Chin Chin Chu (& Timing)": "Mera Naam Chin Chin Chu",\
            "Mere Mitwa Mere Meet (Aaja Tujhko Pukare": "Mere Mitwa Mere Meet",\
            "Mere Rashke Hamar": "Mere Rashke Qamar",\
            "Moh Moh Ke Daage": "Moh Moh Ke Dhage",\
            "Moh Moh Ke Dhaage Dhage": "Moh Moh Ke Dhaage",\
            "Moh Moh Ke Dhage": "Moh Moh Ke Dhaage",\
            "Na Na Karte Pyar Tumhi Jab Jab Phool Khile": "Na Na Karte",\
            "Na Na Karte Pyar Tumhi Se Kar Baithe": "Na Na Karte",\
            "Na Tum Hamein Jaano (Baat Ek Raat Ki": "Na Tum Humein Jano",\
            "Na Tum Hamen Jano": "Na Tum Humein Jano",\
            "Na Tum Humein Jano (Baat Ek Raat Ki": "Na Tum Humein Jano",\
            "Na Tum Jaano Na Hum Reprise": "Na Tum Jano Na Hum",\
            "Na Tum Jano Na Hum": "Na Tum Jaano Na Hum",\
            "Nazm Nazm Sa": "Nazm Nazm",\
            "O Haseena Zulfo Wali": "O Haseena Zulfon Wali",\
            "O Hasina Julfo Wali Jane Jaha": "O Haseena Zulfon Wali",\
            "O Neend Na Mujhko Aaye": "Neend Na Mujhko Aaye",\
            "O Saathi Re Kishore Kumar": "O Saathi Re",\
            "O Saathi Re Tere Bina Bhi Kya Jeena": "O Saathi Re",\
            "O Sathi Re": "O Saathi Re",\
            "Originalabhi Na Jao Chodkar": "Abhi Na Jao Chodkar",\
            "Pahla Nasha Pehla Khumaar": "Pehla Nasha",\
            "Pahla Nasha": "Pehla Nasha",\
            "Pal Pal Dil Ke Dil Ke Paas": "Pal Pal Dil Ke",\
            "Pal Pal Dil Ke Paas Dil Ke Paas": "Pal Pal Dil Ke",\
            "Pal Pal Dil Ke Paas Tum Rahati Ho": "Pal Pal Dil Ke",\
            "Pal Pal Dil Ke Paas Tum Rehti Ho": "Pal Pal Dil Ke",\
            "Pal Pal Dil Ke Paas": "Pal Pal Dil Ke",\
            "Pal Pal Dil Ke Tum Rahati Ho": "Pal Pal Dil Ke",\
            "Pal Pal Dil Ke Tum Rehti Ho": "Pal Pal Dil Ke",\
            "Pal Paldil": "Pal Pal Dil Ke",\
            "Pardesi Pardesi ~": "Pardesi Pardesi",\
            "Pardesi PardesiHd": "Pardesi Pardesi",\
            "Pardesiya Yeh Sach Hain Piya": "Pardesiya Ye Sach Hai Piya",\
            "Payalay Chunmun Virasat": "Payalay Chunmun",\
            "Payali Chunmun": "Payalay Chunmun",\
            "Pehla Nasha Khumaar": "Pehla Nasha",\
            "Pehla Nasha Khumar": "Pehla Nasha",\
            "Pehla Nasha Pehla Khumaar": "Pehla Nasha",\
            "Pehla Nasha Pehla Khumar": "Pehla Nasha",\
            "Pehla Nasha Pehla": "Pehla Nasha",\
            "Phoolon Ke Rang Se (Prem Pujari)": "Phoolon Ke Rang Se",\
            "Phoolon Ke Rang Se Dil Ki Kalam Se": "Phoolon Ke Rang Se",\
            "Pyar Hua Iqrar Hua (Shre 420)": "Pyar Hua Iqrar Hua",\
            "PyarDeewana Hota Hai": "Pyar Deewana Hota Hai",\
            "Qq Ae Mere Humsafar": "Ae Mere Humsafar",\
            "Raat Kali Ek Khwab Me Aayi": "Raat Kali",\
            "Raat Kali Ek Khwab Men Aai": "Raat Kali",\
            "Raat Kali Ek Khwab": "Raat Kali",\
            "Raat Kali Ek": "Raat Kali",\
            "Raat Kali Khwab Me Aayi": "Raat Kali",\
            "Raat Kali Khwab Men Aai": "Raat Kali",\
            "Raat Kali Khwab": "Raat Kali",\
            "Raat Kali Me Aayi": "Raat Kali",\
            "Radha Kese Na Jale": "Radha Kaise Na Jale",\
            "Raja Ko Rani Se Pyar": "Raja Ko Rani Se",\
            "Remix Likhe Jo Khat Tujhe": "Likhe Jo Khat Tujhe",\
            "Rim Jhim Gire Saawan": "Rimjhim Gire Sawan",\
            "Rim Jhim Gire Sawon": "Rimjhim Gire Sawan",\
            "Rimjhim Gire Sawan Music Teacher": "Rimjhim Gire Sawan",\
            "Rimjhim Gire Swn": "Rimjhim Gire Sawan",\
            "Rimzhim Gire Saawan": "Rimjhim Gire Sawan",\
            "Roop Tera Mastaana Remix": "Roop Tera",\
            "Roop Tera Mastaana": "Roop Tera",\
            "Roop Tera Mastana Remix": "Roop Tera",\
            "Roop Tera Mastana": "Roop Tera",\
            "Ruk Jaana Nahi Tu Kahin Haarke": "Ruk Jaana Nahi",\
            "Ruk Jana Nahi": "Ruk Jaana Nahi",\
            "Saans Mei Teri Saans Mili To": "Saans",\
            "Saans Mein Teri": "Saans",\
            "Salame Is Meri Jaan": "Salame Ishq Meri Jaan",\
            "Sawan Barse Tarse Dil (Dahek)": "Sawan Barse Tarse Dil",\
            "Sawan Ka Mahina": "Saawan Ka Mahina",\
            "Shola Jo Bhadke Dil Mera Dhadke": "Shola Jo Bhadke",\
            "Sun Raha Hai Raha": "Sun Raha Hai",\
            "Sun Raha Hai Na Tu  Sun Raha": "Sun Raha Hai",\
            "Sunta Hai Mera Khuda( Original)": "Sunta Hai Mera Khuda",\
            "Suraj Hua Maddham Original Sound": "Suraj Hua Maddham",\
            "Suraj Hua Maddham Original": "Suraj Hua Maddham",\
            "Suraj Hua Madham Original Sound": "Suraj Hua Maddham",\
            "Suraj Hua Madham Original": "Suraj Hua Maddham",\
            "Suraj Hua Madham": "Suraj Hua Maddham",\
            "Suraj Huamadham Maddham": "Suraj Hua Maddham",\
            "Tauba Tumhare Ye Ishare": "Tauba Tumhare Yeh Ishare",\
            "Taubatumhare": "Tauba Tumhare",\
            "Tere Bina Zindagi Se (": "Tere Bina Zindagi Se",\
            "Tere Bina Zindagi Se Koi (": "Tere Bina Zindagi Se",\
            "Tere Bina Zindagi Se Koi": "Tere Bina Zindagi Se",\
            "Tere Bina Zindagi Se Koyi": "Tere Bina Zindagi Se",\
            "Tere Bina Zindagi Set": "Tere Bina Zindagi Se",\
            "Tere Bina Zindgi Se Koyi": "Tere Bina Zindagi Se",\
            "Tere Ghar Ke Saamne Ek Ghar Banaunga": "Tere Ghar Ke Saamne",\
            "Tere Is Mein Nachenge": "Tere Ishq Mein Nachenge",\
            "Tere Liye Hum Hai Jiye": "Tere Liye",\
            "Tere Liye Hum Hain Jiye": "Tere Liye",\
            "Tere Liye Veer Zaara": "Tere Liye",\
            "Tere Mast Mast Do Naain": "Tere Mast Mast Do Nain",\
            "Tere Mere Milan Ki Yeh Raina(Abhimaan)": "Tere Mere Milan Ki Ye Raina",\
            "Tere Mere Sapne Ab Ek Rang Hai (Guide)": "Tere Mere Sapne",\
            "Teri Bindiya Re Teri Bindya Re": "Teri Bindiya Re",\
            "Teri Chunariya Dil Le Gayi": "Teri Chunariya",\
            "Teri Chunariya Dil Le": "Teri Chunariya",\
            "Teri Chunariya Gayi": "Teri Chunariya",\
            "Teri Meri Prem Kahani": "Teri Meri",\
            "Teri Pyari Pyari Surat Ko": "Teri Pyari Pyari Soorat Ko",\
            "Theheriye Hosh Me Aa Lun": "Theheriye Hosh Mein Aa Loon",\
            "Thehriye Hosh Mein Aa Loon": "Theheriye Hosh Mein Aa Loon",\
            "Thoda Sa Pyar Hua Hai + Lirik": "Thoda Sa Pyar Hua Hai",\
            "Thodasa Pyar Hua Hai": "Thoda Sa Pyar Hua Hai",\
            "Thora Sa Pyaar Hua Hai": "Thoda Sa Pyar Hua Hai",\
            "Thuje Dekha Tu Yeh Jaana Sanam": "Tujhe Dekha To",\
            "Tu Aata Hai": "Kaun Tujhe",\
            "Tu Hi Re (Unwind": "Tu Hi Re",\
            "Tu Mile Dil Dil": "Tu Mile Dil Mile",\
            "Tu Nazm Nazm Sa Mere": "Nazm Nazm",\
            "Tu Tu Hai Wahi Rack": "Tu Tu Hai Wahi",\
            "Tu Tu Hai Wahi The Unwind Mix Original": "Tu Tu Hai Wahi",\
            "Tu Tu Hai Wohi The Unwind Mix Original": "Tu Tu Hai Wahi",\
            "Tu Tu Hai Wohi": "Tu Tu Hai Wahi",\
            "Tu Tu Hain Wohi": "Tu Tu Hai Wahi",\
            "Tuje Yaad Na Meri Aayi": "Tujhe Yaad Na Meri Aaye",\
            "Tujh Mein Rab Dikhta Hai  Female": "Tujh Mein Rab Dikhta Hai",\
            "Tujhe Dekha To Dekha": "Tujhe Dekha To",\
            "Tujhe Dekha To Ye Jana Sanam": "Tujhe Dekha To",\
            "Tujhe Dekha To Yeh Jana Sanam": "Tujhe Dekha To",\
            "Tujhe Dekha Todekha": "Tujhe Dekha To",\
            "Tujhe Dekha Tosssf": "Tujhe Dekha To",\
            "Tum He Ho": "Tum Hi Ho",\
            "Tum Hi Ho  Tum": "Tum Hi Ho",\
            "Tum Hi Ho  Tumhi Ho": "Tum Hi Ho",\
            "Tum Hi Ho Tum Hi": "Tum Hi Ho",\
            "Tum Hi Hohi Ho": "Tum Hi Ho",\
            "Tum Itna Jo  Ghazal": "Tum Itna Jo",\
            "Tum Itna Jo Muskura Rahe Ho": "Tum Itna Jo",\
            "Tum Ko Dekha To Ye Khayal (Original)": "Tumko Dekha To Ye Khayal",\
            "Vaste": "Vaaste",\
            "Wo Hai Zara Khafa Khafa": "Woh Hai Zara Khafa Khafa",\
            "Yaad Kiya Dil Ne Hindi Song": "Yaad Kiya Dil Ne",\
            "Yaad Kiya Dil Ne Kahan Hindi Song": "Yaad Kiya Dil Ne",\
            "Yaadaa Rahihai": "Yaad Aa Rahi Hai",\
            "Ye Di Hum Nahi ( )": "Ye Di Hum Nahi",\
            "Ye Dil Tum Bin Hum Kya": "Ye Dil Tum Bin",\
            "Ye Dil Tum Bin Kahin Lagta Nahin Hum Kya": "Ye Dil Tum Bin",\
            "Ye Dil Tum Bin Kahin Lagta Nahin": "Ye Dil Tum Bin",\
            "Ye Mera Prem Patra Padhkar": "Yeh Mera Prem Patra Padh Kar",\
            "Ye Moh Moh Ke Dhage": "Moh Moh Ke Dhaage",\
            "Ye Moh Moh Ke": "Moh Moh Ke Dhaage",\
            "Ye Raat Bheegi Bheegi": "Yeh Raat Bheegi Bheegi",\
            "Ye Raat Ye Chaandni Phir": "Yeh Raat Yeh Chandni Hai Phir Kahan",\
            "Ye Raat Ye Chandni Phir Kaha": "Yeh Raat Yeh Chandni Hai Phir Kahan",\
            "Ye Raatein Ye Mausam Dilli Ka Thug": "Yeh Raatein Yeh Mausam",\
            "Ye Raatein Ye Mausam": "Yeh Raatein Yeh Mausam",\
            "Ye Ratein Ye Mausam": "Yeh Raatein Yeh Mausam",\
            "Ye Sama": "Yeh Sama Sama Hai Ye",\
            "Ye Samaa": "Yeh Sama Sama Hai Ye",\
            "Yediltumbin": "Ye Dil Tum Bin",\
            "Yeh Dil Sun Raha Hai Unwind Mix": "Yeh Dil Sun Raha Hai",\
            "Yeh Ladka Hai Deewana Terbaik": "Yeh Ladka Hai Deewana",\
            "Yeh Raatein Yeh Mausam Dilli Ka Thug": "Yeh Raatein Yeh Mausam",\
            "Yeh Raatein Yeh Mausam Original": "Yeh Raatein Yeh Mausam",\
            "Yeh Raaten Yeh Mausam": "Yeh Raatein Yeh Mausam",\
            "Yeh Sama Sama Hai Ye Pyar Ka": "Yeh Sama Sama Hai Ye",\
            "Yeh Sama Sama Hai Yea": "Yeh Sama Sama Hai Ye",\
            "Zahnaseeb": "Zehnaseeb",\
            "Zara Sa Jhoom Loon Main": "Zara Sa Jhoom Loon",\
            "Zindagi Pyar Ka Geet Hai": "Zindagi Pyar Ka",\
            "{Hd} Rimjhim Gire Sawan": "Rimjhim Gire Sawan",\
            "{Hd} Tu Hi Re": "Tu Hi Re",\
            "{Hd}Hothon Se Chhu Lo Tum": "Hothon Se Chhu Lo Tum",\
            "☛Sun Raha Hai Na Tu☚ ▫ ▫ ▫ ▫ Sun Raha": "Sun Raha Hai",\
            "🙏 Tumhi Mere Mandir": "Tumhi Mere Mandir",\
        }
    return d
