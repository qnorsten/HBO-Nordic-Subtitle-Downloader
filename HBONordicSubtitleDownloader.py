#Script to download subtitles from HBO Nordic
#usage HBONordicSubtitleDownloader.py <url>
#Requires
#*Python3
#*Requests
#*BeautifulSoup4
#Works with episode urls, seasonurls or showpageurls as long as the url ends with an id such as: 99bee710-f406-4a98-a319-f929eedbdabf
#Example Whole series url =https://se.hbonordic.com/cloffice/client/web/browse/5408e6ca-474a-4638-9f35-fe5e67e00737
#Example season url = "https://api-hbon.hbo.clearleap.com/cloffice/client/web/browse/3bc87b76-737d-4c32-8d1b-8d0257c1e7c8"
#Example one episode url = "https://se.hbonordic.com/series/gomorrah/season-1/episode-1/1f10ced-005e3fa02dc"

import sys
import re
import unicodedata
import argparse
import json
import base64
import os
import uuid
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup as Soup

__version__ = '0.2.0'

class HBONordicSubtitleDownloader():
    def __init__(self):
        self.url = args.url
        self.no_srt = args.no_srt
        self.no_xml = args.no_xml
        self.languages = args.languages
        self.username = args.username
        self.password = args.password
        self.device_token = None
        self.get_auth_headers()

    def get_auth_headers(self):
        if os.path.isfile('auth_codes.json'):
            with open('auth_codes.json', 'rb') as f:
                data = json.load(f)
            self.device_id = data.get('device_id',uuid.uuid4())
            self.device_token = data['device_token']
        else:
            self.device_id = uuid.uuid4().urn[9:]
            self.login()

    #originaly copied from svtplay-dl (https://github.com/spaam/svtplay-dl)
    def ensure_unicode(self,s):
        """
        Ensure string is a unicode string. If it isn't it assumed it is
        utf-8 and decodes it to a unicode string.
        """
        #if (is_py2 and isinstance(s, str)) or (is_py3 and isinstance(s, bytes)):
        if isinstance(s, bytes):
            s = s.decode('utf-8', 'replace')
        return s


    def filenamify(self, title):
        """
        Convert a string to something suitable as a file name. E.g.
         Matlagning del 1 av 10 - Räksmörgås | SVT Play
           ->  matlagning.del.1.av.10.-.raksmorgas.svt.play
        """
        # ensure it is unicode
        title = self.ensure_unicode(title)

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


    def saveFile(self, filename, data):

        with open(filename, 'w', encoding='utf-8') as fd:
            fd.write(data)
           
    def saveSubtitle(self, filename, subUrl):
        r = requests.get(subUrl)
        if self.checkLanguage(subUrl) == 'SV':
            filename+="-SV"
        elif self.checkLanguage(subUrl) == 'NO':
            filename+="-NO"
        elif self.checkLanguage(subUrl) == 'DA':
            filename+="-DA"
        elif self.checkLanguage(subUrl) == 'FI':
            filename+="-FI"
       #add else here later
        filename = self.filenamify(filename)
        if not self.no_xml:
            print("Saving: %s.xml" %filename)
            self.saveFile(filename +'.xml',r.text)
        if not self.no_srt:
            srt = self.convertToSrt(r.text)
            print("Saving: %s.srt" %filename)
            self.saveFile(filename+'.srt',srt)

    def checkLanguage(self,subtitleUrl):
        if subtitleUrl.endswith('SV.xml'):
            return 'SV'
        elif subtitleUrl.endswith('NO.xml'):
            return 'NO'
        elif subtitleUrl.endswith('DA.xml'):
            return 'DA'
        elif subtitleUrl.endswith('FI.xml'):
            return 'FI'

    #Converts xml subtitle to srt subtitle 
    def convertToSrt(self,data):
        
        soup = Soup(data,'html.parser')
        plist = soup.findAll('p')
        data = ''
        i = 1
        for p in plist:
            begin = p.get('begin').replace(".", ",")
            end = p.get('end').replace(".", ",")
            begin = re.sub(r'(\d{2}:\d{2}:\d{2}):(\d{2})',r'\1.\2',begin)
            end = re.sub(r'(\d{2}:\d{2}:\d{2}):(\d{2})',r'\1.\2',end)
            data += '%s\n%s --> %s\n' % (i, begin.replace(".", ","), end.replace(".", ","))
            data += p.getText(separator='\n') 
            data += "\n\n"
            i+=1
        return data
       



    def login(self):
        encoded_login = '{}:{}'.format(self.username, base64.b64encode(self.password.encode()).decode())
        encoded_login = base64.b64encode(encoded_login.encode())
        login_url = 'https://api-hbon.hbo.clearleap.com:443/cloffice/client/device/login?language=sv_hbon'
        login_headers = {
            'X-Clearleap-DeviceId': self.device_id,
            'X-Client-Name': 'web',
            'X-Client-Version': '3.8.3',
            'Authorization': 'Basic {}'.format(encoded_login.decode())
        }
        payload = '<device><type>web</type><deviceId>{}</deviceId></device>'.format(self.device_id)
        login = requests.post(login_url, headers=login_headers, data=payload)
        if login.status_code != 200:
            raise ValueError('Unable to login, is supplied username and password correct?')
        soup = Soup(login.content, 'html.parser')
        self.device_token = soup.find('token').contents[0]

        self.saveFile('auth_codes.json', json.dumps({'device_id': self.device_id, 'device_token': self.device_token}))

    def getAndSaveSubtitles(self,url=None):

        if not self.device_token:
            self.login()

        ##Main function
        headers = {}

        headers['X-Clearleap-DeviceToken'] = self.device_token
        headers['X-Clearleap-DeviceId'] = self.device_id
        headers['X-Client-Name'] = 'web'
        headers['X-Client-Version'] = '3.8.3'

        #Example Whole series url =https://se.hbonordic.com/cloffice/client/web/browse/5408e6ca-474a-4638-9f35-fe5e67e00737
        #Example season url = "https://api-hbon.hbo.clearleap.com/cloffice/client/web/browse/3bc87b76-737d-4c32-8d1b-8d0257c1e7c8"
        #Example one episode url = "https://se.hbonordic.com/series/gomorrah/season-1/episode-1/1f10ced-005e3fa02dc"
        if not url:
            url = self.url
        parse = urlparse(url)
        #extract ID and use it
        id = parse.path.split('/')[-1]
        if not id:
            print("Can not find ID in url")
            sys.exit(0)

        #Might replace parse.scheme with http to avoid https in the future
        url = parse.scheme + '://' + parse.netloc
        url = urljoin(url, 'cloffice/client/web/browse/'+ id)
        #get XML with links to subtitles
        data = requests.get(url, headers=headers)
        if data.status_code != 200:
            self.login()
            data = requests.get(url, headers=headers)
        data = data.content
        soup = Soup(data,'html.parser')

        #Find each episode
        items = soup.findAll('item')
        seasonLinks = []
        for item in items: 
            subTitleUrls = item.findAll('media:subtitle')
            #If on season page or episode page
            
            if subTitleUrls:
                #Generates a filename
                #if TV-series (might improve this check later)
                if item.find('clearleap:season'):
                    episode = item.find('clearleap:episodeinseason').text
                    episode = "{:02d}".format(int(episode)) 
                    series = item.find('clearleap:series').text
                    season = item.find('clearleap:season').text
                    season = "{:02d}".format(int(season))
                    filename = '%s.S%sE%s' % (series, season,episode) 
                #If movie
                else:
                    title = item.find('title').text
                    filename = title
                for sub in subTitleUrls:
                    subUrl = sub.get("href")
                    lang = sub.get("lang").replace('_hbon', '')
                    if self.languages:
                        if lang in self.languages:
                            self.saveSubtitle('{}.{}'.format(filename, lang), subUrl)
                    else:
                        self.saveSubtitle('{}.{}'.format(filename, lang), subUrl)
            #if on show page take season urls and call this function again
            else:
                try:
                    if item.find('media:keywords').contents[0] == 'season':
                        # print(item)
                        seasonLink = item.find('link').contents
                        seasonLinks.append(seasonLink[0])
                except AttributeError:
                    pass
        if seasonLinks:    
            for seasonLink in seasonLinks:
                #Prevent loop in case a video is missing subtitles
                if not seasonLink == url:
                    self.getAndSaveSubtitles(seasonLink)
        


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download subtitles from hbo nordic")
    parser.add_argument("url",help="The url to the movie or series to download subtitles from")
    parser.add_argument("--version", help="Displays the current version",action='version', version=__version__)
    parser.add_argument("-u, --username", help="email used to login", dest='username')
    parser.add_argument("-p, --password", help="password", dest='password')
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--no-srt",help="Do not convert downloaded subtitle to srt",action="store_true")
    group.add_argument("--no-xml",help="Do not save the raw xml subtitle",action="store_true")
    parser.add_argument("--languages",help="Specify languages to save in two letter country code as used by HBO Nordic ",nargs='+',choices=['SV','DA','NO','FI'])
    args = parser.parse_args()

    HBO = HBONordicSubtitleDownloader()

    HBO.getAndSaveSubtitles()
    sys.exit(0)
    
    #look up this link later if needed http://stackoverflow.com/questions/20021693/how-to-pass-argparse-arguments-to-a-class
    #args_dict = vars(args)



