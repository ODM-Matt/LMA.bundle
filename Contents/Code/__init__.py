#Live Music Archive (from archive.org) plugin for plex media server

# copyright 2009 Billy Joe Poettgen
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# background image is from http://commons.wikimedia.org/wiki/File:Justice_in_concert.jpg
# icon/cover by Jay Del Turco

import string
import datetime

LOSSLESS_CAPABLE = [ClientPlatform.MacOSX, ClientPlatform.Windows]
RECENT_SHOWS = "http://www.archive.org/search.php?query=collection%3Aetree%26sort%3D-%2Fmetadata%2Fpublicdate"
MOST_DOWNLOADED = "http://www.archive.org/search.php?query=%28%28collection%3Aetree%20OR%20mediatype%3Aetree%29%20AND%20NOT%20collection%3AGratefulDead%29%20AND%20-mediatype%3Acollection&sort=-downloads"
MOST_DOWNLOADED_WEEK = "http://www.archive.org/search.php?query=%28%28collection%3Aetree%20OR%20mediatype%3Aetree%29%20AND%20NOT%20collection%3AGratefulDead%29%20AND%20-mediatype%3Acollection&sort=-week"
ARTISTS_URL = "http://www.archive.org/advancedsearch.php?q=mediatype%3Acollection+collection%3Aetree&fl[]=creator&fl[]=identifier&sort[]=identifier+asc&sort[]=&sort[]=&rows=50000&page=1&fmt=xml&xmlsearch=Search#raw"

###################################################################################################
def Start():
  Plugin.AddPrefixHandler('/music/LMA', MainMenu, 'Live Music Archive', 'icon-default.png', 'art-default.jpg')
  Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
  Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
  ObjectContainer.title1 = 'Live Music Archive'
  ObjectContainer.content = 'Items'
  ObjectContainer.art = R('art-default.jpg')
  DirectoryObject.thumb=R('icon-default.png')
  HTTP.CacheTime = CACHE_1HOUR

###################################################################################################

def MainMenu():
  oc = ObjectContainer(view_group='List')
  oc.add(DirectoryObject(key=Callback(Letters), title="Browse Archive by Artist"))
  '''TODO >>> write a LMA Search Service'''
  #dir.Append(Function(InputDirectoryItem(showList, title="Seach the Live Music Archive", prompt="Search..."), title2="Search Results"))
  
  oc.add(DirectoryObject(key=Callback(ShowList, title2="This Day in History", pageURL=Callback(TodayURL())), title="Shows This Day in History"))
  oc.add(DirectoryObject(key=Callback(ShowList, title2="Recently Added Shows", pageURL=RECENT_SHOWS), title="Most Recently Added Shows"))
  oc.add(DirectoryObject(key=Callback(ShowList, title2="Most Downloaded", pageURL=MOST_DOWNLOADED), title="Most Downloaded Shows"))
  oc.add(DirectoryObject(key=Callback(ShowList, title2="Last Week", pageURL=MOST_DOWNLOADED_WEEK), title="Most Downloaded Shows Last Week"))
  oc.add(DirectoryObject(key=Callback(Staff), title="Staff Picks"))
  
  if itunesPage() != None:
    oc.add(ObjectDirectory(key=Callback(iTunes), title="Find Shows for Artists in my iTunes Library"))
    oc.add(PrefsObject("Preferences...",
           summary="No PMS instance with a valid iTunes library at this address (default: localhost)\n Please enter the IP address of a PMS instance sharing an iTunes library.",
           thumb=S('Gear.png')))
  else:
    oc.add(PrefsObject("Preferences...", thumb=S('Gear.png')))
  return oc

##################################################################################################

def Letters():
  oc = ObjectContainer(title2="Artists", view_group='List')
  oc.add(DirectoryObject(key=Callback(Artists, letter="#"), title="#"))
  for c in list(string.ascii_uppercase):
    oc.add(DirectoryObject(key=Callback(Artists, letter=c), title=c))

  return oc

##################################################################################################

def Artists(letter=None):
  oc = ObjectContatiner(title2="Artists-%s" % letter, view_group='List')

  artistsList = XML.ElementFromURL(ARTISTS_URL, errors='ignore',)
  results = artistsList.xpath("/response//doc")
  for n in range(len(results)):
    identifier = artistsList.xpath("//doc[%i]/str[@name='identifier']/text()"  % (n+1))
    name = artistsList.xpath("//doc[%i]/arr[@name='creator']/str/text()"  % (n+1))
    if identifier != []:
      identifier = str(identifier[0])
    else:
      continue
    if name != []:
      name = str(name[0])
    else:
      continue
    if letter=="#":
      for n in list(string.digits):
        if identifier[0] == n:
          pageURL= "http://www.archive.org/search.php?query=collection%3A" + identifier + "&sort=-date&page=1"
          oc.add(DirectoryObject(key=Callback(ShowList, pageURL=pageURL, title2=name, isArtistPage=True, identifier=identifier), title=name))
    else:
      if identifier[0] == letter:
        pageURL= "http://www.archive.org/search.php?query=collection%3A" + identifier + "&sort=-date&page=1"
        oc.add(DirectoryObject(key=Callback(ShowList, pageURL=pageURL, title2=name, isArtistPage=True, identifier=identifier), title=name))

  return oc

##################################################################################################

def ShowList(title2, pageURL=None, isArtistPage=False, identifier=None, query=None, thumbs=None):
  oc = MediaContainer(title2=title2, view_group='List')
  if thumbs == None:
    thumbs = R('icon-default.png')
  if query != None:
    query = String.URLEncode(query)
    pageURL="http://www.archive.org/search.php?query="+query+"%20AND%20collection%3Aetree"
  
  
  showsList = HTML.ElementFromURL(pageURL, errors='ignore')
  if showsList != None:

    # auto detect show numbers and split by year if high
    if isArtistPage == True:
      numShows = showsList.xpath("//div[3]//tr[2]//td[1]//b[2]//text()")
      if numShows != []:
        numShows = int(numShows[0].replace(",",""))
        if numShows >= 51:
          # get the years list
          yearsPage = HTML.ElementFromURL("http://www.archive.org/browse.php?collection=" + identifier + "&field=year", errors="ignore")
          years = yearsPage.xpath("//table[@id='browse']//ul//a/text()")
          yearURLs = yearsPage.xpath("//table[@id='browse']//ul//a/@href")
          for year, url in zip(years, yearURLs):
            oc.add(DirectoryObject(key=Callback(ShowList, title2=str(year), pageURL="http://www.archive.org" + url + "&sort=date"), title=str(year), thumb=thumbs))
          return oc


    showURLs = showsList.xpath("//a[@class='titleLink']/@href")
    showTitles = showsList.xpath("//a[@class='titleLink']")
    # pain in my fucking ass roundabout way to get propper show titles for artists split by date
    titles = []
    for i in range(len(showTitles)):
      y = showsList.xpath("//table[@class='resultsTable']//tr[%i]/td[2]/a[1]//text()" % (i+1))
      # the +1 is because python list indexes start from 0 and indexes in xpath start at 1
      title = ''.join(y)
      titles.append(title)
    
    for url, title in zip(showURLs, titles):        
      
      # for artists in the search results
      if showsList.xpath("//a[@class='titleLink'][@href='%s']/parent::td/preceding-sibling::td/img[@alt='[collection]']" %url):
        pageURL= "http://www.archive.org/search.php?query=collection%3A" + url.replace("/details/","") + "&sort=-date&page=1"
        oc.add(DirectoryObject(key=Callback(ShowList, pageURL=pageURL, title2=title, isArtistPage=True, identifier=url.replace("/details/","")), title=title))

      else:
        ### REFERENCES TO "Concert()" SHOULD BE REPLACED WITH "AlbumObject()"s POINTING TO THE URL SERVICE TO RETRIEVE "TrackObject()"s ###
        oc.add(DirectoryObject(key=Callback(Concert, page=str(url), showName=str(title)), title=str(title), thumb=thumbs))

    next = showsList.xpath("//a[text()='Next']/@href")
    if next != []:
      pageURL = "http://www.archive.org" + next[0]
      oc.add(ObjectDirectory(key=Callback(ShowList, pageURL=pageURL, title2=title2), title="Next 50 Results"))

  return oc

##################################################################################################

### REFERENCES TO "Concert()" SHOULD BE REPLACED WITH "AlbumObject()"s POINTING TO THE URL SERVICE TO RETRIEVE "TrackObject()"s ###
def Concert(sender, page, showName):
  dir = MediaContainer(title2=showName)
  page = HTML.ElementFromURL("http://www.archive.org" + page, errors="ignore")
  artist = str(page.xpath("//div[3]/a[3]/text()")).strip("[]'")
  album = str(page.xpath("//span[text()='Date:']/following-sibling::*[1]/text()")).strip("[]'")
  urls = []
  
  #get mp3s
  media_type = page.xpath("//table[@id='ff2']//tr[1]//td[text()='VBR MP3']")
  if media_type != []:
    i = len(media_type[0].xpath('preceding-sibling::*')) 
    urls = page.xpath("//table[@id='ff2']//tr/td[%i]/a/@href" % (i+1))
    Log("found mp3s")

  if Client.Platform in LOSSLESS_CAPABLE:
    #get flac16, shn
    if Prefs['lossless'] == True:
      media_type = page.xpath("//table[@id='ff2']//tr[1]//td[text()='Flac']")
      Log("looking for Flac")
      if media_type != []:
        i = len(media_type[0].xpath('preceding-sibling::*')) 
        urls = page.xpath("//table[@id='ff2']//tr/td[%i]/a/@href" % (i+1))
        Log("found Flacs")
      elif media_type == []:
        media_type = page.xpath("//table[@id='ff2']//tr[1]//td[text()='Shorten']")
        Log("looking for shorten")
        if media_type != []:
          i = len(media_type[0].xpath('preceding-sibling::*')) 
          urls = page.xpath("//table[@id='ff2']//tr/td[%i]/a/@href" % (i+1))
          Log("found shn")
  
    #Get FLAC24
    if Prefs['flac24'] == True:
      media_type = page.xpath("//table[@id='ff2']//tr[1]//td[text()='24bit Flac']")
      Log("looking for Flac24")
      if media_type != []:
        i = len(media_type[0].xpath('preceding-sibling::*')) 
        urls = page.xpath("//table[@id='ff2']//tr/td[%i]/a/@href" % (i+1))
        Log("found Flac24")
  else:
    #client is unable to play lossless formats
    pass
  #get titles
  titles = page.xpath("//table[@id='ff2']//td[1]/text()")
  if titles != []:
    del titles[0]
  
  #append tracks
  if urls != []:
    for url, title in zip(urls, titles):
      dir.Append(TrackItem("http://www.archive.org" + url, title=title.strip(), artist=artist, album=album, thumb=R('icon-default.png')))
  
  # m3u stream fallback for grateful dead soundboards
  else:
    try:
      m3u = page.xpath("//a[text()='VBR M3U']/@href")[0]
      if m3u[0] is not 'h': m3u = 'http://www.archive.org/' + m3u
      m3u = HTTP.Request(m3u).content.strip().splitlines()
      Log('using m3u')
      for url in m3u:
        dir.Append(TrackItem(url, title="Track %i" % (m3u.index(url)+1), artist=artist, album=album, thumb=R('icon-default.png')))
        
    except: Log('nothing found')
  return dir

##################################################################################################
# staff picks top level menu
def Staff():
  oc = ObjectContainer(title2="Staff Picks")
  page = HTML.ElementFromURL("http://www.archive.org/details/etree", errors="ignore")
  titles = page.xpath("//div[@id='picks']//a//text()")
  urls = page.xpath("//div[@id='picks']//a//@href")
  for url, title in zip(urls, titles):
    ### REFERENCES TO "Concert()" SHOULD BE REPLACED WITH "AlbumObject()"s POINTING TO THE URL SERVICE TO RETRIEVE "TrackObject()"s ###
    oc.add(ObjectDirectory(key=Callback(Concert), page=str(url), showName=str(title)), title=str(title))

  return oc

##################################################################################################

def iTunes(sender):
# fuzzy matching way way way way way too slow (estimate 15 minutes for my library), cant even verify it works. exact matches only till plex framework can do the matching
  
  dir = MediaContainer(title2="iTunes")
  itunesURL = "http://" + Prefs['itunesIP'] + ":32400/music/iTunes/Artists"
  itunesArtistsPage = XML.ElementFromURL(itunesURL, errors='ignore')
  if itunesArtistsPage == None:
    return MessageContainer(header="No Itunes Found",  message="no pms instance with a valid itunes library at this address\n(default: localhost) Plese go the the plugin's prefrences and set \nthe ip address of a pms instance sharing an itunes library")
  itunesArtists = itunesArtistsPage.xpath('//Artist/@artist')
  itunesThumbs = itunesArtistsPage.xpath('//Artist/@thumb')
  
  LMAartistsURL = "http://www.archive.org/advancedsearch.php?q=mediatype%3Acollection+collection%3Aetree&fl[]=creator&fl[]=identifier&sort[]=identifier+asc&sort[]=&sort[]=&rows=50000&page=1&fmt=xml&xmlsearch=Search#raw"
  LMAartistsList = XML.ElementFromURL(LMAartistsURL, errors='ignore',)
  results = LMAartistsList.xpath("/response//doc")
  
  itunesDict = {}
  for itunesArtist, itunesThumb in zip(itunesArtists, itunesThumbs):
    itunesArtist = str(itunesArtist).lower().replace(" and ", "").replace("the ", "").replace(" ", "").translate(string.maketrans("",""), string.punctuation)
    itunesDict[itunesArtist] = itunesThumb
  
  for n in range(len(results)):
    identifier = LMAartistsList.xpath("//doc[%i]/str[@name='identifier']/text()"  % (n+1))
    LMAname = LMAartistsList.xpath("//doc[%i]/arr[@name='creator']/str/text()"  % (n+1))
    if identifier != []:
      identifier = str(identifier[0])
    else:
      continue
    if LMAname != []:
      LMAname = str(LMAname[0])
    else:
      continue
    
    
    strippedLMAname = LMAname.lower().replace(" and ", "").replace("the ", "").replace(" ", "").translate(string.maketrans("",""), string.punctuation)
    
    
    if strippedLMAname in itunesDict:
        pageURL= "http://www.archive.org/search.php?query=collection%3A" + identifier + "&sort=-date&page=1"
        thumb = "http://" + Prefs['itunesIP'] + ":32400" +  itunesDict[strippedLMAname]
        
        dir.Append(Function(DirectoryItem(showList, title=LMAname, thumb = thumb), pageURL=pageURL, title2=LMAname, isArtistPage=True, identifier=identifier, thumbs=thumb))
    
  return dir

def TodayURL():
  now = datetime.datetime.now()
  month = str(now.month)
  day = str(now.day)
  if now.month < 10:
    month = '0' + month
  if now.day < 10:
    day = '0' + day
  today_URL = "http://www.archive.org/search.php?query=collection:etree%20AND%20%28date:19??-"+month+"-"+day+"%20OR%20date:20??-"+month+"-"+day+"%29&sort=-/metadata/date"
  return today_URL

def iTunesPage():
  try:
    itunesURL = "http://" + Prefs['itunesIP'] + ":32400/music/iTunes/Artists"
    itunesArtistsPage = XML.ElementFromURL(itunesURL, errors='ignore')
  except:
    itunesArtistsPage = None
  return itunesArtistsPage