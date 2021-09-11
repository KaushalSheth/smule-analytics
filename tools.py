import asyncio
from bs4 import BeautifulSoup
from pyppeteer import launch
import os, time

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

    return {"owners":owner_list,"joiners":joiner_list}

def getHtml(utilitiesOptions):
    url = utilitiesOptions["url"]
    try:
        loop = asyncio.get_running_loop()
    except:
        loop = asyncio.new_event_loop()
    htmlstr = loop.run_until_complete(loadDynamicHtml(url))

    return {"owners":[htmlstr],"joiners":[]}
