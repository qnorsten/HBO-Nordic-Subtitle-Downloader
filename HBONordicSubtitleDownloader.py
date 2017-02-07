#Script to download subtitles from HBO Nordic
#usage HBONordicSubtitleDownloader.py <url>
#Requires
#*Python3
#*Requests
#*BeautifulSoup4
#Works with episode urls, seasonurls or showpageurls as long as the url ends with an id such as: 99bee710-f406-4a98-a319-f929eedbdabf

from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup as Soup
import sys
import re
import unicodedata

#import argparse


#originaly copied from svtplay-dl (https://github.com/spaam/svtplay-dl)
def ensure_unicode(s):
    """
    Ensure string is a unicode string. If it isn't it assumed it is
    utf-8 and decodes it to a unicode string.
    """
    #if (is_py2 and isinstance(s, str)) or (is_py3 and isinstance(s, bytes)):
    if isinstance(s, bytes):
        s = s.decode('utf-8', 'replace')
    return s


def filenamify(title):
    """
    Convert a string to something suitable as a file name. E.g.
     Matlagning del 1 av 10 - Räksmörgås | SVT Play
       ->  matlagning.del.1.av.10.-.raksmorgas.svt.play
    """
    # ensure it is unicode
    #title = ensure_unicode(title)

    # NFD decomposes chars into base char and diacritical mark, which
    # means that we will get base char when we strip out non-ascii.
    title = unicodedata.normalize('NFD', title)

    # Convert to lowercase
    # Drop any non ascii letters/digits
    # Drop any leading/trailing whitespace that may have appeared
    title = re.sub(r'[^a-z0-9 .-]', '', title.lower().strip())

    # Replace whitespace with dot
    title = re.sub(r'\s+', '.', title)
    title = re.sub(r'\.-\.', '-', title)

    return title


def saveFile(filename, data):

    with open(filenamify(filename), 'w') as fd:
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
    saveFile(filename +'.xml',r.text)
    srt = convertToSrt(r.text)
    saveFile(filename+'.srt',srt)



#Converts xml subtitle to srt subtitle 
def convertToSrt(data):
    
    soup = Soup(data,'html.parser')
    plist = soup.findAll('p')
    data = ''
    i = 1
    for p in plist:
        begin = p.get('begin').replace(".", ",")
        end = p.get('end').replace(".", ",")
        data += '%s\n%s --> %s\n' % (i, begin.replace(".", ","), end.replace(".", ","))
        data += p.getText(separator='\n')  #("<br/>-","\n")
        data += "\n\n"
        i+=1
    return data
   


def getAndSaveSubtitles(url):
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

    #Might replace parse.scheme with http to avoid https in the future
    url = parse.scheme + '://' + parse.netloc
    url = urljoin(url, 'cloffice/client/web/browse/'+ id)
    #get XML with links to subtitles
    data = requests.get(url).content
    
    soup = Soup(data,'html.parser')

    #Find each episode
    items = soup.findAll('item')
    seasonLinks = []
    for item in items: 
        subTitleUrls = item.findAll('media:subtitle')
        #If on season page or episode page
        
        if subTitleUrls:
            #Generates a filename
            episode = item.find('clearleap:episodeinseason').text
            episode = "{:02d}".format(int(episode)) 
            series = item.find('clearleap:series').text
            season = item.find('clearleap:season').text
            season = "{:02d}".format(int(season))
            filename = '%s.S%sE%s' % (series, season,episode) 

            for subUrl in subTitleUrls:
                saveSubtitle(filename,subUrl.get("href"))
        #if on show page take season urls
        else:
            seasonLink = item.find('link').contents
            seasonLinks.append(seasonLink[0])
    if seasonLinks:    
        for seasonLink in seasonLinks:
            #Prevent loop in case a video is missing subtitles
            if not seasonLink == url:
                getAndSaveSubtitles(seasonLink)
    


if __name__ == "__main__":

    if len(sys.argv) >= 2:
       url = sys.argv[1]
       #print('url is %s' % url)
       getAndSaveSubtitles(url)
       exit(0)
    else:
        print('You must supply a url')


