#Script to download subtitles from HBO Nordic
#usage HBONordicSubtitleDownloader.py <url>
#Requires
#*Requests
#*BeautifulSoup4
#Works with episode urls, seasonurls or showpageurls as long as the url ends with an id such as: 99bee710-f406-4a98-a319-f929eedbdabf

from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup as Soup
import sys
#import argparse

def saveFile(filename, data):

    with open(filename, 'wb') as fd:
        fd.write(data)
       
def saveSubtitle(filename, subUrl):
    r = requests.get(subUrl, stream=True)
    if subUrl.endswith('SV.xml'):
        filename+="-SE"
    elif subUrl.endswith('NO.xml'):
        filename+="-NO"
    elif subUrl.endswith('DA.xml'):
        filename+="-DK"
    elif subUrl.endswith('FI.xml'):
        filename+="-FI" 
    filename += '.xml'  
    saveFile(filename,r.content)


def getAndSaveSubtitles(url):
    print(url)
    ##Main function
    #extract ID and use it
    #Example Whole series url =https://se.hbonordic.com/cloffice/client/web/browse/5408e6ca-474a-4638-9f35-fe5e67e00737
    #Example season url = "https://api-hbon.hbo.clearleap.com/cloffice/client/web/browse/3bc87b76-737d-4c32-8d1b-8d0257c1e7c8"
    #Example one episode url = "https://se.hbonordic.com/series/gomorrah/season-1/episode-1/1f10ced-005e3fa02dc"
    parse = urlparse(url)
    id = parse.path.split('/')[-1]
    if not id:
        print("Can not find ID")
        exit(-1)

        
    # print(id)
    #get XML with links to subtitles
    url = urljoin('http://se.hbonordic.com/cloffice/client/web/browse/', id)
    data = requests.get(url).content

    #Improve this to find episodenumber (do not know why it doest work)
    soup = Soup(data,'html.parser')
    #Eveyrhting bottom of this can be added to own function to batch whole seasons
    #Find each episode
    items = soup.findAll('item')
    seasonLinks = []
    for item in items: 
        subTitleUrls = item.findAll('media:subtitle')
        #If on season page or episode page
        
        if subTitleUrls:
            #Todo improve filenaming is 
            #episode = soup.find('clearleap:episodeInSeason') #this should be used instead of episode but is not working for some reason
            series = item.find('clearleap:series').text
            season = item.find('clearleap:season').text
            episode = item.find('clearleap:episode').text 
            filename = '%s.S%s.%s' % (series, season,episode) 

            for subUrl in subTitleUrls:
                saveSubtitle(filename,subUrl.get("href"))
        #if on show page take season urls
        else:
            seasonLink = item.find('link').contents
            seasonLinks.append(seasonLink[0])
        
    for seasonLink in seasonLinks:
        #Prevent loop in case a video is missing subtitles
        if not seasonLink == url:
            getAndSaveSubtitles(seasonLink)
    


if __name__ == "__main__":

    if len(sys.argv) >= 2:
       url = sys.argv[1:]
       #print('url is %s' % url)
       getAndSaveSubtitles(url)
    else:
        print('You must supply a url')
    #if sys.argv[1:]
    #url = "https://se.hbonordic.com/cloffice/client/web/browse/5408e6ca-474a-4638-9f35-fe5e67e00737"
    #

