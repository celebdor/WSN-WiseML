"""
This file is part of WSN-visor.

WSN-visor is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

WSN-visor is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with WSN-visor.  If not, see <http://www.gnu.org/licenses/>.
"""
import urllib2
import urllib
from cookielib import CookieJar

url = 'http://meteoroleg.upc.es/dexserver/j_spring_security_check'
urlRep = 'http://meteoroleg.upc.es/dexserver/report-results.htm?6578706f7274=1&d-49653-e=1&queryId=83'
login = { 'j_username': 'lsi-upc', 'j_password': 'lsi-upc' }
headers = {'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US)'}
loginFormData = urllib.urlencode(login)

req = urllib2.Request(url, loginFormData, headers)
resp = urllib2.urlopen(req)

cookies = CookieJar()
cookies.extract_cookies(resp, req) 

cookie_handler = urllib2.HTTPCookieProcessor(cookies)
redirect_handler = urllib2.HTTPRedirectHandler()
opener = urllib2.build_opener(redirect_handler, cookie_handler)
opener.open(req)
req2 =  urllib2.Request(urlRep, dict(), headers)
resp2 = opener.open(req2)

print len(cookies)

for l in resp2:
     print l
