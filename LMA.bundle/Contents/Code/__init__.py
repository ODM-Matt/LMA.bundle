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


import re, string
from PMS import *
from PMS.Objects import *
from PMS.Shortcuts import *

LMA_PREFIX   = "/music/LMA"

CACHE_INTERVAL = 3600


###################################################################################################
def Start():
  Plugin.AddPrefixHandler(LMA_PREFIX, MainMenu, 'Live Music Archive', '', '')
  Plugin.AddViewGroup("InfoList", viewMode="InfoList", mediaType="items")
  Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
  MediaContainer.title1 = 'Live Music Archive'
  MediaContainer.content = 'Items'
  MediaContainer.art = R('')
  Prefs.Add('lossless', 'bool', 'false', L("Prefer Lossless (FLAC16, SHN)"))
  Prefs.Add('flac24', 'bool', 'false', L("Prefer FLAC24 if available (needs pretty fast internet connecion)"))
  HTTP.SetCacheTime(CACHE_INTERVAL)

###################################################################################################
def MainMenu():
	dir = MediaContainer(viewGroup='InfoList')
	dir.Append(Function(DirectoryItem(artists, title="Browse Archive by Artist",)))
#	dir.Append(Function(DirectoryItem(doSearch, title="Seach the Live Music Archive",)))
#	dir.Append(Function(DirectoryItem(today, title="Shows this Day in History",)))
#	dir.Append(Function(DirectoryItem(recent, title="Most Recently Added Shows",)))
#	dir.Append(Function(DirectoryItem(newArtists, title="Recently Added Artists",)))
#	dir.Append(Function(DirectotyItem(mostDown, title="Most Downloaded Shows",)))
#	dir.Append(Function(DirectoryItem(lastWeek, title="Most Downloaded Shows Last Week",)))
#	dir.Append(Function(DirectoryItem(staff, title="Staff Picks",)))

	mainPage = XML.ElementFromURL("http://www.archive.org/details/etree", isHTML=True, errors="ignore")
	spotlightURL = str(mainPage.xpath("//div[@id='spotlight']/a/@href")).strip("[]'")
	name = str(mainPage.xpath("//div[@id='spotlight']/a/text()")).strip("[]'")
	dir.Append(Function(DirectoryItem(concert, title="Spotlight Show", summary=name), page=spotlightURL, showName=name))
	dir.Append(PrefsItem("Preferences..."))
#	dir.Append(Function(DirectoryItem(concert, title="test"), page="/details/eo2004-09-19_24bit", showName="test"))
	return dir	

##################################################################################################


def artists(sender):
	dir = MediaContainer(title2="All Artists", viewGroup='List')
	
	artistsURL = "http://www.archive.org/advancedsearch.php?q=mediatype%3Acollection+collection%3Aetree&fl[]=collection&fl[]=identifier&fl[]=mediatype&sort[]=titleSorter+asc&sort[]=&sort[]=&rows=50000&fmt=xml&xmlsearch=Search#raw"
	artistsList = XML.ElementFromURL(artistsURL, errors='ignore',)
	artists = artistsList.xpath("//str[@name='identifier']/text()")
	for identifier in artists:
		identifier = str(identifier)
		pageURL= "http://www.archive.org/search.php?query=collection%3A" + identifier + "&sort=-date&page=1"
		dir.Append(Function(DirectoryItem(showList, title=identifier), pageURL=pageURL, identifier=identifier))
	return dir

def showList(sender, identifier, pageURL):
	dir = MediaContainer(title2=identifier, viewGroup='List')
	showsList = XML.ElementFromURL(pageURL, isHTML=True, errors='ignore')
	if showsList != None:
		showURLs = showsList.xpath("//a[@class='titleLink']/@href")
		showTitles = showsList.xpath("//a[@class='titleLink']/text()")
		for url, title in zip(showURLs, showTitles):
			dir.Append(Function(DirectoryItem(concert, title=str(title)), page=str(url), showName=str(title)))

	next = showsList.xpath("//a[text()='Next']/@href")
	if next != []:
		pageURL = "http://www.archive.org" + next[0]
		Log(identifier)
		Log(pageURL)
		dir.Append(Function(DirectoryItem(showList, title="Next 50 Results"), pageURL=pageURL, identifier=identifier))

	return dir



def concert(sender, page, showName):
	dir = MediaContainer(title2=showName)
	page = XML.ElementFromURL("http://www.archive.org" + page, isHTML=True, errors="ignore")
	artist = str(page.xpath("/html/body/div[3]/a[3]/text()")).strip("[]'")
	album = str(page.xpath("/html/body/div[5]/div/p[1]/span[6]/text()")).strip("[]'")
	urls = []
	
	#get mp3
	media_type = page.xpath("//table[@id='ff2']//tr[1]//td[text()='VBR MP3']")
	if media_type != []:
		i = len(media_type[0].xpath('preceding-sibling::*')) 
		urls = page.xpath("//table[@id='ff2']//tr/td[%i]/a/@href" % (i+1))
		Log("found mp3s")
	
	
	#get flac16, shn
	if Prefs.Get('lossless') == True:
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
	if Prefs.Get('flac24') == True:
		media_type = page.xpath("//table[@id='ff2']//tr[1]//td[text()='24bit Flac']")
		Log("looking for Flac24")
		if media_type != []:
			i = len(media_type[0].xpath('preceding-sibling::*')) 
			urls = page.xpath("//table[@id='ff2']//tr/td[%i]/a/@href" % (i+1))
			Log("found Flac24")
	
	#get titles
	titles = page.xpath("//table[@id='ff2']//td[1]/text()")
	del titles[0]
	
	#append tracks
	for url, title in zip(urls, titles):
		dir.Append(TrackItem("http://www.archive.org" + url, title=title, artist=artist, album=album))
	
	
	return dir



