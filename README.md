#Script to download subtitles from HBO Nordic
**usage** `HBONordicSubtitleDownloader.py <url>`
##Requires
* Python3
* Requests (http://docs.python-requests.org/en/master/#)
* BeautifulSoup4B (https://www.crummy.com/software/BeautifulSoup/bs4/doc/)

Works with episode urls, seasonurls or showpageurls as long as the url ends with an id such as: 99bee710-f406-4a98-a319-f929eedbdabf
* Example whole series url =https://se.hbonordic.com/cloffice/client/web/browse/5408e6ca-474a-4638-9f35-fe5e67e00737
* Example season url = "https://api-hbon.hbo.clearleap.com/cloffice/client/web/browse/3bc87b76-737d-4c32-8d1b-8d0257c1e7c8"
* Example one episode url = "https://se.hbonordic.com/series/gomorrah/season-1/episode-1/1f10ced-005e3fa02dc"
