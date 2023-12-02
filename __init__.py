import os
import ast
import asyncio

from flask import Flask, render_template, redirect, url_for, request, flash, g
from flask_migrate import Migrate
from .smule import fetchSmulePerformances, downloadSong, crawlUsers, fetchFileTitleMappings, getComments, crawlJoiners, checkPartners, saveSingerFollowing, fetchPartnerInfo, fetchOpenInvites, fetchDBInviteJoins
from .db import fetchDBPerformances, saveDBPerformances, saveDBFavorite, saveDBFavorites, fixDBTitles, fetchDBPerformers, fetchDBTopPerformers, execDBQuery, fetchDBPerformerMapInfo
from .analytics import fetchDBAnalytics
from .invites import fetchPartnerInvites, fetchSongInvites
from .tools import loadDynamicHtml, titlePerformers, getHtml, nonJoiners, titleMetadata, saveTitleMetadata
from datetime import datetime

# Set defaults for global variable that are used in the app
searchOptions = {'solo':False,'contentType':"both",'joins':True,'searchType':"normal",'dbfilter':"1=1"}
analyticsOptions = {'username':"KaushalSheth1",'fromdate':"2018-01-01",'todate':"2030-01-01",'analyticstitle':"Custom",'headings':[],'analyticssql':""}
utilitiesOptions = {'username':"KaushalSheth1",'fromdate':"2018-01-01",'todate':"2030-01-01",'title':"Lag+Ja+Gale",'sort':'popular','distance':"500",'centlat':"37.76",'centlon':"-121.89"}
inviteOptions = {'knowntitles':True,'unknowntitles':False,'repeats':False,'newtitles':False,'partnersql':"select 'KaushalSheth1' as partner_name,1 as sort_order"}
user = None
search_user = None
performances = None
numrows = 200
gTitleMappings = None
rsPartnerInfo = None
fromdate = "2018-01-01"
todate = "2030-01-01"
numrows = 9999

def update_currtime():
    global currtime
    currtime = datetime.now().strftime("%m/%d/%Y %H:%M:%S")

# Create the app and set up all the routes for the various actions that can be taken
def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', default='dev'),
    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    from .models import db

    # Prepare app to work with SQLAlchemy and Flask-Migrate
    db.init_app(app)
    migrate = Migrate(app, db)

    # Main home page of the app
    @app.route('/')
    def index():
        update_currtime()
        return render_template('index.html')

    # This displays performer thumbnails using the existing performances list
    @app.route('/show_performers')
    def show_performers():
        global performances
        update_currtime()
        return render_template('show_performers.html', performers=performances)

    # This method queries the DB for performer thumbnails and basic stats
    @app.route('/query_performers')
    def query_performers():
        performers = fetchDBPerformers(fromdate, todate)
        update_currtime()
        return render_template('show_performers.html', performers=performers)

    # This method queries the DB for top monthly performers for last 20 months
    @app.route('/query_top_performers')
    def query_top_performers():
        performers = fetchDBTopPerformers()
        update_currtime()
        return render_template('top_performers.html', performers=performers)

    # This method checks the list of partners using specified partnersql and lists all the partners I am not following
    @app.route('/check_partners')
    def check_partners():
        global performances, inviteOptions, numrows, searchOptions, performers
        searchOptions['searchType'] = "checkpartners"
        performers = checkPartners(inviteOptions)
        update_currtime()
        return render_template('show_performers.html', performers=performers)

    # The search page allows you to search for performances either in the Smule site or the DB
    @app.route('/search', methods=('GET','POST'))
    def search():
        global user, numrows, search_user, startoffset, fromdate, todate, searchtype, searchOptions, inviteOptions
        update_currtime()

        # When the form is posted, store the form field values into global variables
        if request.method == 'POST':
            # Initialize search options dict to empty
            searchOptions = {}
            error = None

            # Set all search options
            if request.form.get('offline'):
                searchOptions['offline'] = True
            else:
                searchOptions['offline'] = False
            if request.form.get('solo'):
                searchOptions['solo'] = True
            else:
                searchOptions['solo'] = False
            if request.form.get('joins'):
                searchOptions['joins'] = True
            else:
                searchOptions['joins'] = False
            if request.form.get('comments'):
                searchOptions['comments'] = True
            else:
                searchOptions['comments'] = False
            if request.form.get('audio') and request.form.get('videos'):
                searchOptions['contentType'] = "both"
            elif request.form.get('audio'):
                searchOptions['contentType'] = "audio"
            elif request.form.get('videos'):
                searchOptions['contentType'] = "video"
            else:
                searchOptions['contentType'] = "none"
            user = request.form['username']
            if not user:
                error = "Username is required."
            search_user = user
            numrows = int(request.form['numrows'])
            startoffset = int(request.form['startoffset'])
            fromdate = request.form['fromdate']
            todate = request.form['todate']
            searchtype = 'PERFORMANCES'
            dbfilter = request.form['dbfilter']
            if dbfilter:
                searchOptions['dbfilter'] = dbfilter
            dbinvitedays = request.form['dbinvitedays']
            if dbinvitedays:
                searchOptions['dbinvitedays'] = dbinvitedays

            # Set all invite options
            inviteOptions['partnerchoice'] = request.form['partnerchoice']
            inviteOptions['partnersql'] = request.form['partnersql']
            if request.form.get('knowntitles'):
                inviteOptions['knowntitles'] = True
            else:
                inviteOptions['knowntitles']  = False
            if request.form.get('unknowntitles'):
                inviteOptions['unknowntitles'] = True
            else:
                inviteOptions['unknowntitles']  = False
            if request.form.get('repeats'):
                inviteOptions['repeats'] = True
            else:
                inviteOptions['repeats']  = False
            if request.form.get('notfollowing'):
                inviteOptions['notfollowing'] = True
            else:
                inviteOptions['notfollowing']  = False
            if request.form.get('newtitles'):
                inviteOptions['newtitles'] = True
            else:
                inviteOptions['newtitles']  = False
            if request.form.get('inclpartner'):
                inviteOptions['inclpartner'] = True
            else:
                inviteOptions['inclpartner']  = False
            inviteOptions['maxknown'] = int(request.form['maxknown'])
            inviteOptions['maxunknown'] = int(request.form['maxunknown'])
            inviteOptions['dayslookback'] = int(request.form['dayslookback'])
            inviteOptions['maxsongs'] = int(request.form['maxsongs'])
            inviteOptions['maxperf'] = int(request.form['maxperf'])
            inviteOptions['title'] = request.form['title']

            # Depending on which button was clicked, take the appropriate action
            if error is None:
                # Refresh title mappings
                if request.form['btn'] == 'Search Smule':
                    searchtype = 'PERFORMANCES'
                    return redirect(url_for('query_smule_performances'))
                elif request.form['btn'] == 'Search Favorites':
                    searchtype = 'FAVORITES'
                    #return redirect(url_for('query_smule_favorites'))
                    return redirect(url_for('query_db_favorites', username=f"{user}:s"))
                elif request.form['btn'] == 'Search Ensembles':
                    searchtype = 'ENSEMBLES'
                    return redirect(url_for('query_smule_ensembles'))
                elif request.form['btn'] == 'DB Invite Joins':
                    return redirect(url_for('db_invite_joins'))
                elif request.form['btn'] == 'Search Invites':
                    searchtype = 'INVITES'
                    return redirect(url_for('query_smule_invites'))
                elif request.form['btn'] == 'Search Performers':
                    return redirect(url_for('query_performers'))
                elif request.form['btn'] == 'Top Performers':
                    return redirect(url_for('query_top_performers'))
                elif request.form['btn'] == 'Search DB':
                    return redirect(url_for('query_db_performances', searchtype='srchuser', searchval=user))
                elif request.form['btn'] == 'Crawl Joiners':
                    return redirect(url_for('crawl_joiners', username=user))
                elif request.form['btn'] == 'Fix Titles':
                    return redirect(url_for('fix_db_titles'))
                elif request.form['btn'] == 'Update Following':
                    return redirect(url_for('update_singer_following'))
                elif request.form['btn'] == 'Get Partner Info':
                    return redirect(url_for('get_partner_info'))
                elif request.form['btn'] == 'Partner Invites':
                    return redirect(url_for('query_partner_invites'))
                elif request.form['btn'] == 'Song Invites':
                    return redirect(url_for('query_song_invites'))
                elif request.form['btn'] == 'Check Partners':
                    return redirect(url_for('check_partners'))
                else:
                    error = "Invalid selection"

            # If any errors were detected during the post, disaply the erorr message
            flash(error, 'error')

        # When the form is fetched, initialize the global variables and display the search form
        user = None
        performances = None
        return render_template('search.html')

    # This method is referenced in the list_performances HTML page in order to fetch performances for the owner listed
    @app.route('/search_smule_user/<username>')
    def search_smule_user(username):
        global user, searchtype
        user = username
        if searchtype == 'FAVORITES':
            return redirect(url_for('query_smule_favorites'))
        elif searchtype == 'ENSEMBLES':
            return redirect(url_for('query_smule_ensembles'))
        else:
            return redirect(url_for('query_smule_performances'))

    # The utilities page allows you to execute one of the utilities
    @app.route('/utilities', methods=('GET','POST'))
    def utilities():
        global user, utilitiesOptions
        update_currtime()

        # When the form is posted, store the form field values into global variables
        if request.method == 'POST':
            toolName = request.form["btn"]
            utilitiesOptions['title'] = request.form["title"].replace(" ","+")
            utilitiesOptions['url'] = request.form["url"]
            utilitiesOptions['distance'] = request.form["distance"]
            utilitiesOptions['dayssincelastperf'] = request.form["dayssincelastperf"]
            utilitiesOptions['centlat'] = request.form["centlat"]
            utilitiesOptions['centlon'] = request.form["centlon"]
            if toolName == "Recent Performers":
                return redirect(url_for('title_performers', sort='recent'))
            elif toolName == "Popular Performers":
                return redirect(url_for('title_performers', sort='popular'))
            elif toolName == "Get HTML":
                return redirect(url_for('get_html'))
            elif toolName == "Download":
                return redirect(url_for('download_song'))
            elif toolName == "Performer Map":
                return redirect(url_for('performer_map'))
            elif toolName == "Non Joiners":
                return redirect(url_for('non_joiners'))
            elif toolName == "Title Metadata":
                return redirect(url_for('title_metadata'))
            elif toolName == "Save Title Metadata":
                return redirect(url_for('save_title_metadata'))

        # When the form is fetched, initialize the global variables and display the search form
        user = None
        return render_template('utilities_choice.html')

    # The Analytics page allows you to choose one of the analytics "reports" you wish to display
    @app.route('/analytics', methods=('GET','POST'))
    def analytics():
        global user, searchtype, analyticsOptions
        update_currtime()
        searchtype = 'ANALYTICS'

        # When the form is posted, store the form field values into global variables
        if request.method == 'POST':
            error = None
            user = request.form['username']
            if not user:
                error = "Username is required."

            analyticsOptions['username'] = user
            analyticsOptions['fromdate'] = request.form['fromdate']
            analyticsOptions['todate'] = request.form['todate']
            analyticsTitle = request.form['btn']
            analyticsOptions['analyticstitle'] = analyticsTitle
            analyticsOptions['timeperiod'] = request.form['timeperiod']

            if (analyticsTitle == "Custom"):
                headingsStr = request.form['headings']
                if not headingsStr:
                    error = "Column Headings is required and needs to be specified as list of strings matching the output of the SQL"
                else:
                    # The assumption is that the heading string will be a list, so evaluate it and convert it to a list to pass as the headings option
                    headingsList =  ast.literal_eval(headingsStr)
                    analyticsOptions['headings'] = headingsList
                    analyticsOptions['analyticssql'] = request.form['analyticssql']

            # If no errors on page, query analytics
            if error is None:
                return redirect(url_for('query_analytics'))

            # If any errors were detected during the post, disaply the erorr message
            flash(error, 'error')

        # When the form is fetched, initialize the global variables and display the search form
        user = None
        analytics = None
        return render_template('analytics_choice.html')

    # This method queries the DB for title analytics using the relevant global variables
    @app.route('/title_performers/<sort>')
    def title_performers(sort):
        global toolsOutput, utilitiesOptions
        utilitiesOptions['sort'] = sort
        toolsOutput = titlePerformers(utilitiesOptions)
        flash(f"{len(toolsOutput['list1'])} owners and {len(toolsOutput['list2'])} joiners fetched from Smule")
        return redirect(url_for('tools_output'))

    # This method queries the DB for title analytics using the relevant global variables
    @app.route('/non_joiners/')
    def non_joiners():
        global toolsOutput, utilitiesOptions
        toolsOutput = nonJoiners(utilitiesOptions)
        flash(f"{len(toolsOutput['list1'])} non-joiners fetched from Smule")
        return redirect(url_for('tools_output'))

    # This method queries an external service for metadata about the specified title
    @app.route('/title_metadata/')
    def title_metadata():
        global toolsOutput, utilitiesOptions
        toolsOutput = titleMetadata(utilitiesOptions)
        flash(f"{len(toolsOutput['list1'])} titles fetched from Smule")
        return redirect(url_for('tools_output'))

    # This method queries an external service for metadata about the specified title
    @app.route('/save_title_metadata/')
    def save_title_metadata():
        global toolsOutput, utilitiesOptions
        toolsOutput = saveTitleMetadata()
        flash(f"{len(toolsOutput['list1'])} title metadata updated")
        return redirect(url_for('tools_output'))

    # This method queries the DB for title analytics using the relevant global variables
    @app.route('/get_html')
    def get_html():
        global toolsOutput, utilitiesOptions

        toolsOutput = getHtml(utilitiesOptions)
        flash(f"{len(toolsOutput['owners'])} owners and {len(toolsOutput['joiners'])} joiners fetched from Smule")
        return redirect(url_for('tools_output'))

    # This method queries the DB for performer map info and displays it
    @app.route('/performer_map')
    def performer_map():
        global utilitiesOptions

        performerMapInfo = fetchDBPerformerMapInfo(utilitiesOptions)
        flash(f"{len(performerMapInfo)} performers fetched from DB")
        return render_template('map.html', performances=performerMapInfo, options=utilitiesOptions)

    # This method queries the DB for title analytics using the relevant global variables
    @app.route('/query_analytics')
    def query_analytics():
        global headings, analytics, analyticsOptions
        # Fetch the analytics into a global variable, display a message indicating how many were fetched, and display them
        # Using a global variable for analytics allows us to easily reuse the same HTML page for listing analytics
        headings,analytics = fetchDBAnalytics(analyticsOptions)
        flash(f"{len(analytics)} rows fetched from database")
        return redirect(url_for('analytics_output'))

    # Generic route for displaying analytics using global variables
    @app.route('/tools_output')
    def tools_output():
        global toolsOutput, currtime, utilitiesOptions
        # This assumes that the analytics global variable is set by the time we get here
        return render_template('tools_output.html', toolsOutput=toolsOutput, currtime=currtime, title=utilitiesOptions["title"])

    # Generic route for displaying analytics using global variables
    @app.route('/analytics_output')
    def analytics_output():
        global analytics, user, currtime, headings, analyticsOptions
        # This assumes that the analytics global variable is set by the time we get here
        return render_template('analytics_output.html', headings=headings, analytics=analytics, user=user, currtime=currtime, analyticstitle=analyticsOptions['analyticstitle'])

    # This method is referenced in the list_performances HTML page in order to fetch favorites for the owner listed
    @app.route('/crawl_joiners/<username>')
    def crawl_joiners(username):
        global fromdate, todate
        # Call method that will fetch joiner list from DB and then fetch all performances for these joiners within specified date range
        message = crawlJoiners(username,fromdate,todate)
        flash(message)
        return redirect(url_for('search'))

    # This method is referenced in the list_performances HTML page in order to fetch favorites for the owner listed
    @app.route('/crawl_favorites/<username>')
    def crawl_favorites(username):
        global user, numrows, performances, startoffset, fromdate, todate
        # Fetch the performances into a global variable, display a message indicating how many were fetched, and display them
        # Using a global variable for performances allows us to easily reuse the same HTML page for listing performances
        message = crawlUsers(username,performances,numrows,startoffset,fromdate,todate,searchType="favorites")
        flash(message)
        return redirect(url_for('list_performances'))

    # This method is referenced in the list_performances HTML page in order to fetch performances for the owner listed
    @app.route('/crawl_performances/<username>')
    def crawl_performances(username):
        global user, numrows, performances, startoffset, fromdate, todate
        # Fetch the performances into a global variable, display a message indicating how many were fetched, and display them
        # Using a global variable for performances allows us to easily reuse the same HTML page for listing performances
        message = crawlUsers(username,performances,numrows,startoffset,fromdate,todate,searchType="performances")
        flash(message)
        return redirect(url_for('list_performances'))

    # This method fetches a list of partners using specified partnersql and then fetches all invites by these partners
    @app.route('/query_partner_invites')
    def query_partner_invites():
        global performances, inviteOptions, numrows, searchOptions
        searchOptions['searchType'] = "partnerinvites"
        performances = fetchPartnerInvites(inviteOptions,inviteOptions['maxsongs'])
        flash(f"{len(performances)} performances fetched from Smule")
        return redirect(url_for('list_performances'))

    # This method fetches a list of invites for all known songs that have not yet been sung in the current month
    @app.route('/query_song_invites')
    def query_song_invites():
        global performances, inviteOptions, numrows, searchOptions
        searchOptions['searchType'] = "songinvites"
        performances = fetchSongInvites(inviteOptions,inviteOptions['maxsongs'])
        flash(f"{len(performances)} performances fetched from Smule")
        return redirect(url_for('list_performances'))

    # This executes smule function to get partner information (number of joins, etc.)
    @app.route('/get_partner_info')
    def get_partner_info():
        global rsPartnerInfo, rsOpenInvites, rsInviteJoins
        rsOpenInvites, rsInviteJoins = fetchOpenInvites()
        rsPartnerInfo = fetchPartnerInfo()
        flash(f"{len(rsPartnerInfo)} partner info rows retrieved from DB")
        return redirect(url_for('search'))

    # This executes the smule function to fetch all performances using global variables set previously
    @app.route('/query_smule_performances')
    def query_smule_performances():
        global user, numrows, performances, startoffset, fromdate, todate, searchOptions, rsPartnerInfo
        searchOptions['searchType'] = "normal"
        if rsPartnerInfo == None:
            rsPartnerInfo = fetchPartnerInfo()
        # Fetch the performances into a global variable, display a message indicating how many were fetched, and display them
        # Using a global variable for performances allows us to easily reuse the same HTML page for listing performances
        performances = fetchSmulePerformances(user,numrows,startoffset,"recording",fromdate,todate,searchOptions)
        flash(f"{len(performances)} performances fetched from Smule")
        return redirect(url_for('list_performances'))

    # This executes the smule function to fetch all performances using global variables set previously
    @app.route('/query_smule_invites')
    def query_smule_invites():
        global user, numrows, performances, startoffset, fromdate, todate, invites, searchOptions
        searchOptions['searchType'] = "normal"
        # Fetch the performances into a global variable, display a message indicating how many were fetched, and display them
        # Using a global variable for performances allows us to easily reuse the same HTML page for listing performances
        performances = fetchSmulePerformances(user,numrows,startoffset,"invites",fromdate,todate)
        flash(f"{len(performances)} invites fetched from Smule")
        return redirect(url_for('list_invites'))

    # This executes the smule function to fetch favorite performances using global variables set previously
    # Luckily for us, the structure of all performances and favorite performances is the same, so we can reuse the objects
    @app.route('/query_smule_favorites')
    def query_smule_favorites():
        global user, numrows, performances, startoffset, fromdate, todate, searchOptions, rsPartnerInfo
        searchOptions['searchType'] = "normal"
        if rsPartnerInfo == None:
            rsPartnerInfo = fetchPartnerInfo()
        # Fetch the performances into a global variable, display a message indicating how many were fetched, and display them
        # Using a global variable for performances allows us to easily reuse the same HTML page for listing performances
        performances = fetchSmulePerformances(user,numrows,startoffset,"favorites",fromdate,todate)
        flash(f"{len(performances)} performances fetched from Smule")
        return redirect(url_for('list_performances'))

    # This executes the smule function to fetch favorite ensemble performances using global variables set previously
    # This basically queries all performances but then only includes the ones that are ensembles
    @app.route('/query_smule_ensembles')
    def query_smule_ensembles():
        global user, numrows, performances, startoffset, fromdate, todate
        # Fetch the performances into a global variable, display a message indicating how many were fetched, and display them
        # Using a global variable for performances allows us to easily reuse the same HTML page for listing performances
        performances = fetchSmulePerformances(user,numrows,startoffset,"ensembles",fromdate,todate)
        flash(f"{len(performances)} performances fetched from Smule")
        return redirect(url_for('list_performances'))

    # This executes the smule function to fetch DB invites and then look for new joins in Smule
    @app.route('/db_invite_joins')
    def db_invite_joins():
        global user, performances, fromdate, todate, searchOptions
        # Fetch the performances into a global variable, display a message indicating how many were fetched, and display them
        # Using a global variable for performances allows us to easily reuse the same HTML page for listing performances
        performances = fetchDBInviteJoins(user,int(searchOptions['dbinvitedays']))
        flash(f"{len(performances)} joins fetched from Smule")
        return redirect(url_for('list_performances'))

    # This method tags the specified performance as a favorite
    @app.route('/save_db_favorite/<perfkey>/<rating>')
    def save_db_favorite(perfkey,rating):
        global user, performances
        retVal = saveDBFavorite(user,perfkey,rating)
        return str(retVal)

    # This executes the db function to fetch performances using global variables set previously
    @app.route('/query_db_performances/<searchtype>/<searchval>')
    def query_db_performances(searchtype,searchval):
        global user, numrows, performances, fromdate, todate, gTitleMappings, searchOptions
        # Load global variable for title mappings from file
        gTitleMappings = fetchFileTitleMappings('TitleMappings.txt')
        # Set DB Filter based on searchtype
        if searchtype == 'srchuser':
            searchOptions['dbfilter'] = "1 = 1"
            username = searchval
        else:
            fromdate = "2001-01-01"
            todate = "2030-01-01"
            if searchtype == 'user':
                searchOptions['dbfilter'] = "1 = 1"
                username = searchval
            elif searchtype == 'joins':
                searchOptions['dbfilter'] += " and join_ind = 1"
                username = searchval
            elif searchtype == 'title':
                searchOptions['dbfilter'] = f"fixed_title ilike '{searchval}'"
                username = ""
            elif searchtype == 'titlejoins':
                searchOptions['dbfilter'] = f"fixed_title ilike '{searchval}' and join_ind = 1"
                username = ""
            else:
                searchOptions['dbfilter'] = "1 = 1"
                username = ""
        # Fetch the performances into a global variable, display a message indicating how many were fetched, and display them
        # Using a global variable for performances allows us to easily reuse the same HTML page for listing performances
        performances = fetchDBPerformances(username,numrows,fromdate,todate,gTitleMappings,searchOptions)
        flash(f"{len(performances)} performances fetched from database")
        return redirect(url_for('list_performances'))

    # This executes the db function to fetch favorites from DB using global variables set previously
    @app.route('/query_db_favorites/<username>')
    def query_db_favorites(username):
        global user, numrows, performances, fromdate, todate, gTitleMappings, searchOptions
        # Load global variable for title mappings from file
        gTitleMappings = fetchFileTitleMappings('TitleMappings.txt')
        # Set DB Filter to only include favorites
        searchOptions['dbfilter'] += " and favorite_ind = 1"
        # If the username contains ":s" at hte end, it came from the search page, so strip it out from username and leave from/to dates alone. If there isn't a ":s" at the end, it came form analytics page, so set from/to date to min/max values
        if ":s" in username:
            username = username.split(":")[0]
        else:
            fromdate = "2001-01-01"
            todate = "2030-01-01"
        # Fetch the performances into a global variable, display a message indicating how many were fetched, and display them
        # Using a global variable for performances allows us to easily reuse the same HTML page for listing performances
        performances = fetchDBPerformances(username,numrows,fromdate,todate,gTitleMappings,searchOptions)
        flash(f"{len(performances)} performances fetched from database")
        return redirect(url_for('list_performances'))

    # This executes the db function to fix titles in the DB
    @app.route('/fix_db_titles')
    def fix_db_titles():
        global gTitleMappings
        # Load global variable for title mappings from file
        gTitleMappings = fetchFileTitleMappings('TitleMappings.txt')
        # Fix the titles using this global variable
        fixCount = fixDBTitles(gTitleMappings)
        flash(f"{fixCount} titles fixed in database")
        return redirect(url_for('search'))

    # This executes the db function to update Singer_Following in the DB
    @app.route('/update_singer_following')
    def update_singer_following():
        global user
        # Update Singer Following
        msg = saveSingerFollowing(user)
        flash(f"{msg}")
        return redirect(url_for('search'))

    # This gets the comments for the specified web url
    @app.route('/get_comments')
    def get_comments():
        global weburl
        # Load global variable for title mappings from file
        commentStr = getComments(weburl)
        flash(f"{commentStr}")
        return redirect(url_for('search'))

    # This method allows us to take various actions on the list of performances displayed
    @app.route('/submit_performances', methods=('GET','POST'))
    def submit_performances():
        global user, performances, rsPartnerInfo, rsOpenInvites, rsInviteJoins
        # We can save the listed performances/favorites to the DB, download them all, or display them on a map (using leaflet)
        if request.form['btn'] == 'Save Performances':
            message = saveDBPerformances(user,performances)
            rsPartnerInfo = fetchPartnerInfo()
            rsOpenInvites, rsInviteJoins = fetchOpenInvites()
        elif request.form['btn'] == 'Save Favorites':
            message = saveDBFavorites(user,performances)
        elif request.form['btn'] == 'Download All':
            message = download_all_performances()
        elif request.form['btn'] == 'Show Map':
            return render_template('map.html', performances=performances)
        else:
            error = "Invalid source - valid options are 'smule' and 'db'"
        flash(message)
        return redirect(url_for('list_performances'))

    # Generic route for displaying performances using global variable
    @app.route('/list_performances')
    def list_performances():
        global performances, search_user, user, download, searchOptions
        # This assumes that the performances global variable is set by the time we get here
        return render_template('list_performances.html', performances=performances, search_user=search_user, user=user, searchOptions=searchOptions)

    # Generic route for displaying performances using global variable
    @app.route('/list_invites')
    def list_invites():
        global performances, search_user, user, invites, currtime

        # This assumes that the performances global variable is set by the time we get here
        return render_template('list_invites.html', performances=performances, search_user=search_user, user=user, currtime=currtime)

    # Method to download the performance to local disk
    @app.route('/download_performance/<key>')
    def download_performance(key):
        global performances, user
        # Look up the performance by key in the global list of performances
        performance = next(item for item in performances if item['key'] == key)
        # Downlod the song to /tmp (hardcoded for now)
        # TODO: Allow specification of download folder as well as add error handling for key not found
        retVal = downloadSong(performance["web_url"], "/tmp/", performance['filename'],performance,user)
        if retVal == 0:
            flash("Successfully downloaded to /tmp/" + performance['filename'])
        #return redirect(url_for('list_performances'))
        return str(retVal)

    # Method to download the performance to local disk
    @app.route('/download_song')
    def download_song():
        global user, utilitiesOptions
        web_url = utilitiesOptions["url"]
        # Set filename to last part of the web_url, which should be the performace key
        filename = web_url.split("/")[-1] + ".m4a"
        # Downlod the song to /tmp (hardcoded for now)
        retVal = downloadSong(web_url, "/tmp/", filename ,None, user)
        if retVal == 0:
            flash("Successfully downloaded to /tmp/" + filename)
        return str(retVal)

    # Route to downlaod all performances - this could potentially be moved to the smule module
    @app.route('/download_all_performances')
    def download_all_performances():
        global performances, user
        i = 0
        numFails = 0
        failedSongs = []
        for performance in performances:
            print("=======================================================================")
            print(f"{i} - {performance['web_url_full']}")
            result = 0
            # Only download joins for ensembles, not the invite itself
            if performance["create_type"] != "invite":
                result = downloadSong(performance["web_url_full"], "/tmp/", performance['filename'],performance,user)
                if result == 0:
                    i += 1
                else:
                    numFails += 1
                    failedSongs.append(performance['filename'])
        retVal = f"Successfully downloaded {i} songs to /tmp; {numFails} downloads failed"
        if len(failedSongs) > 0:
            retVal += "\nFailed to download: " + ', '.join(failedSongs)
        print(retVal)
        return retVal

    return app
