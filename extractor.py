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
import urllib2, sys, urllib, re
from cookielib import CookieJar
from dateutil.parser import parse
from xml import etree
import pickle

class trace:
     times = dict()
#Parsing preparation
#Date hour:min nodeId nodeName traceId readingType* value
     pattern = re.compile( '(.*?)/(.*?)/(.*?) (.*?),(.*?),(.*?),(.*?),(.*?),"(.*?),(.*?)"' )
     search = trace.pattern.search

     @staticmethod
     def getTime(string):
          try:
               return trace.times[string]
          except KeyError:
               t = parse(string)
               trace.times[string] = t
               return t

     def __init__(self, rhs):
          try:
               self.traceId = rhs.traceId
               self.time = rhs.time
               self.nodeId = rhs.nodeId
               self.name = rhs.name
               self.temp = rhs.temp
               self.hum = rhs.hum
               self.lum = rhs.lum
          except AttributeError: 
               s = trace.search(rhs)
               self.traceId = s.group(7)
               self.time = trace.getTime(s.group(3)+'-'+s.group(2)+'-'+s.group(1)+'T'+s.group(4)+'+01:00')
               self.nodeId = s.group(5)
               self.name = s.group(6)
               kind = s.group(8)
               self.temp = None
               self.hum = None
               self.lum = None
               if kind == 'temperatura':
                    self.temp = float(s.group(9)+'.'+s.group(10)) 
               elif kind == 'humitat':
                    self.hum = float(s.group(9)+'.'+s.group(10)) 
               elif kind == 'lluminositat':
                    self.lum = float((s.group(9).replace('.',''))+'.'+s.group(10)) 

     def __add__(lhs, rhs):
          if rhs.temp is not None:
               lhs.temp = rhs.temp
          if rhs.hum is not None:
               lhs.hum = rhs.hum
          if rhs.lum is not None:
               lhs.lum = rhs.lum
          return lhs

     def hash(self):
          return (self.time, self.nodeId)

     def __eq__(lhs, rhs):
          return lhs.nodeId == rhs.nodeId and lhs.time == rhs.time

     def __str__(self):
          return '('+str(self.time)+':'+self.nodeId+'_'+self.name+')->'+str(self.temp)+'C '+str(self.hum)+'% '+str(self.lum)+'LUX'

class experiment:
     def __init__(self):
          self.traces = dict()

     def __init__(self, rhs):
          try:
               self.traces = rhs.traces
          except AttributeError:
               self.traces = dict()
               rhs = trace(rhs)
               self+=rhs

     def __add__(lhs, rhs):
          h = rhs.hash()
          try:
               #print lhs.traces[h], rhs
               lhs.traces[h] += rhs
          except KeyError:
               lhs.traces[h] = rhs
          return lhs

     def __contains__(lhs, rhs):
          for e in lhs.traces:
               if e == rhs:
                    return True
          return False
     
     def __str__(self):
          return '\n'.join([str(t) for t in self.traces.values()])+'\n\n'
     
def traceProcess(lhs, rhs):
     return experiment(lhs)+trace(rhs)

if sys.argv[3] == 'get':
     url = 'http://meteoroleg.upc.es/dexserver/j_spring_security_check'
     urlTemp = 'http://meteoroleg.upc.es/dexserver/report-results.htm?6578706f7274=1&d-49653-e=1&queryId=83'
     urlHum = 'http://meteoroleg.upc.es/dexserver/report-results.htm?6578706f7274=1&d-49653-e=1&queryId=84'
     urlLum = 'http://meteoroleg.upc.es/dexserver/report-results.htm?6578706f7274=1&d-49653-e=1&queryId=85'
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
     reqLum =  urllib2.Request(urlLum, dict(), headers)
     respTemp = opener.open(reqTemp)
     respHum = opener.open(reqHum)
     respLum = opener.open(reqLum)

     fl = open('list_obj','wb')
     l = list(respTemp)
     l.extend(respHum)
     l.extend(respLum)
     pickle.dump(l, fl)
else:
     fl = open('list_obj','rb')
     l = pickle.load(fl)


trRed = reduce(traceProcess, l)

print trRed
