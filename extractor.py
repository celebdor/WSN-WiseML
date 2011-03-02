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
import urllib2, sys, urllib
from cookielib import CookieJar

url = 'http://meteoroleg.upc.es/dexserver/j_spring_security_check'
urlTemp = 'http://meteoroleg.upc.es/dexserver/report-results.htm?6578706f7274=1&d-49653-e=1&queryId=83'
urlHum = 'http://meteoroleg.upc.es/dexserver/report-results.htm?6578706f7274=1&d-49653-e=1&queryId=84'
urlLight = 'http://meteoroleg.upc.es/dexserver/report-results.htm?6578706f7274=1&d-49653-e=1&queryId=85'
login = { 'j_username': sys.argv[1] , 'j_password': sys.argv[2] }
headers = {'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US)'}
loginFormData = urllib.urlencode(login)

req = urllib2.Request(url, loginFormData, headers)
resp = urllib2.urlopen(req)

cookies = CookieJar()
cookies.extract_cookies(resp, req) 

cookie_handler = urllib2.HTTPCookieProcessor(cookies)
redirect_handler = urllib2.HTTPRedirectHandler()
opener = urllib2.build_opener(redirect_handler, cookie_handler)
#Making the initial connection for the login
opener.open(req)
reqTemp =  urllib2.Request(urlTemp, dict(), headers)
reqHum =  urllib2.Request(urlHum, dict(), headers)
reqLight =  urllib2.Request(urlLight, dict(), headers)
respTemp = opener.open(reqTemp)
respHum = opener.open(reqHum)
respLight = opener.open(reqLight)

ft = open('y_temp.csv','w')
fh = open('y_hum.csv','w')
fl = open('y_lum.csv','w')

for l in respTemp:
     ft.write(l)
for l in respHum:
     fh.write(l)
for l in respLight:
     fl.write(l)

ft.close()
fh.close()
fl.close()
