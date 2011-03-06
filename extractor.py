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
from lxml import etree
from optparse import OptionParser
import pickle
import datetime
from operator import attrgetter

class trace:
     times = dict()
#Parsing preparation
#Date hour:min nodeId nodeName traceId readingType* value
     pattern = re.compile( '(.*?)/(.*?)/(.*?) (.*?):(.*?),(.*?),(.*?),(.*?),(.*?),"(.*?),(.*?)"' )
     search = pattern.search

     @classmethod
     def getTime(cls, tup):
          try:
               return cls.times[tup]
          except KeyError:
               t = datetime.datetime(*tup)
               cls.times[tup] = t
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
               self.traceId = s.group(8)
               self.time = trace.getTime((int(s.group(3)), int(s.group(2)),int(s.group(1)),int(s.group(4)),int(s.group(5))))
               self.nodeId = s.group(6)
               self.name = s.group(7)
               kind = s.group(9)
               self.temp = None
               self.hum = None
               self.lum = None
               if kind == 'temperatura':
                    self.temp = float(s.group(10)+'.'+s.group(11)) 
               elif kind == 'humitat':
                    self.hum = float(s.group(10)+'.'+s.group(11)) 
               elif kind == 'lluminositat':
                    self.lum = float((s.group(10).replace('.',''))+'.'+s.group(11)) 

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

     def toXml(self):
          e = etree.Element('node')
          e.attrib['id'] = 'urn:wisebed:upc:'+self.nodeId
          temp = etree.SubElement(e, 'data')
          temp.attrib['key'] = 'urn:wisebed:upc:node:capability:temperature'
          temp.text = str(self.temp)
          hum = etree.SubElement(e, 'data')
          hum.attrib['key'] = 'urn:wisebed:upc:node:capability:humidity'
          hum.text = str(self.hum)
          lum = etree.SubElement(e, 'data')
          lum.attrib['key'] = 'urn:wisebed:upc:node:capability:light'
          lum.text = str(self.lum)
          return e

class experiment:
     nodes = dict()

     @classmethod
     def trackNodes(cls, rhs):
          cls.nodes[rhs.nodeId] = rhs.name

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
               lhs.traces[h] += rhs
          except KeyError:
               lhs.traces[h] = rhs
               experiment.trackNodes(rhs)
          return lhs

     def __contains__(lhs, rhs):
          for e in lhs.traces:
               if e == rhs:
                    return True
          return False
     
     def __str__(self):
          return '\n'.join([str(t) for t in self.traces.values()])+'\n\n'

     def generateXmlSetup(self, it, et):
          s = etree.Element('setup')
          time = etree.SubElement(s, 'timeinfo')
          startTime = etree.SubElement(time, 'start')
          startTime.text = it.isoformat()
          endTime = etree.SubElement(time, 'end')
          endTime.text = et.isoformat()
          timeUnit = etree.SubElement(time, 'unit')
          timeUnit.text = 'seconds'
          for n in experiment.nodes:
               node = etree.SubElement(s, 'node')
               node.attrib['id'] = 'urn:wisebed:upc:'+n
#position
               pos = etree.SubElement(node, 'position')
               x = etree.SubElement(pos, 'x')
               x.text = '1.0'
               y = etree.SubElement(pos, 'y')
               y.text = '1.0'
               z = etree.SubElement(pos, 'z')
               z.text = '1.0'
#Gateway
               gateway = etree.SubElement(node, 'gateway')
               gateway.text = 'false'
#programDetails
               gateway = etree.SubElement(node, 'programDetails')
               gateway.text = 'Environmental conditions tracking software'
#nodeType
               gateway = etree.SubElement(node, 'nodeType')
               gateway.text = 'dexcell'
#description
               gateway = etree.SubElement(node, 'description')
               gateway.text = experiment.nodes[n]
#Capabilities
               cTemp = etree.SubElement(node, 'capability')
               cTempName = etree.SubElement(cTemp, 'name')
               cTempName.text = 'urn:wisebed:upc:node:capability:temperature' 
               cTempDataType = etree.SubElement(cTemp, 'datatype')
               cTempDataType.text = 'decimal'
               cTempUnit = etree.SubElement(cTemp, 'unit')
               cTempUnit.text = 'degrees'
               cTempDefault = etree.SubElement(cTemp, 'default')
               cTempDefault.text = '0'

               cHum =  etree.SubElement(node, 'capability')
               cHumName = etree.SubElement(cHum, 'name')
               cHumName.text = 'urn:wisebed:upc:node:capability:humidity' 
               cHumDataType = etree.SubElement(cHum, 'datatype')
               cHumDataType.text = 'decimal'
               cHumUnit = etree.SubElement(cHum, 'unit')
               cHumUnit.text = 'percentage'
               cHumDefault = etree.SubElement(cHum, 'default')
               cHumDefault.text = '0'

               cLum =  etree.SubElement(node, 'capability')
               cLumName = etree.SubElement(cLum, 'name')
               cLumName.text = 'urn:wisebed:upc:node:capability:light' 
               cLumDataType = etree.SubElement(cLum, 'datatype')
               cLumDataType.text = 'decimal'
               cLumUnit = etree.SubElement(cLum, 'unit')
               cLumUnit.text = 'lux'
               cLumDefault = etree.SubElement(cLum, 'default')
               cLumDefault.text = '0'
          return s

     def toXml(self):
          traceList =  self.traces.values()
          traceList.sort(key=attrgetter('time'), reverse=False)
          it = traceList[0].time
          lt = traceList[len(traceList)-1].time
          pd = datetime.timedelta(-1)
          root = etree.Element('wiseml')
          root.attrib['version'] = '1.0'
          root.attrib['xmlns'] = 'http://wisebed.eu/ns/wiseml/1.0'
          root.append(self.generateXmlSetup(it, lt))
          for e in  traceList:
               t = e.time-it
               if pd != t:
                    ts = etree.Element('timestamp')
                    ts.text = str(t.seconds)
                    root.append(ts)
                    pd = t
               root.append(e.toXml())
          return root
          
     
class dataFetcher:
     def __init__(self):
          self.l = list()

     def fetchSerialized(self, filename = 'list_obj.o'):
          try:
               fl = open(filename, 'rb')
          except IOError:
               print >> sys.stderr, 'The file ', filename, ' was not found'
               sys.exit(0)
          try:
               self.l = pickle.load(fl)
          except:
               print >> sys.stderr, 'The file ', filename, 'is not a extractor object'
               sys.exit(0)
          fl.close()

     def fetchNetData(self, username, password):
          url = 'http://meteoroleg.upc.es/dexserver/j_spring_security_check'
          urlTemp = 'http://meteoroleg.upc.es/dexserver/report-results.htm?6578706f7274=1&d-49653-e=1&queryId=83'
          urlHum = 'http://meteoroleg.upc.es/dexserver/report-results.htm?6578706f7274=1&d-49653-e=1&queryId=84'
          urlLum = 'http://meteoroleg.upc.es/dexserver/report-results.htm?6578706f7274=1&d-49653-e=1&queryId=85'
          login = { 'j_username': username , 'j_password': password }
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
          self.l.extend(respTemp)
          self.l.extend(respHum)
          self.l.extend(respLum)

     def serialize(self, filename = 'list_obj.o'):
          try:
               fl = open(filename, 'wb')
          except IOError:
               print >> sys.stderr, 'Failed to write to ', filename
               sys.exit(0)
          pickle.dump(self.l, fl)
          fl.close()
          
     def data(self):
          return self.l

def traceProcess(lhs, rhs):
     return experiment(lhs)+trace(rhs)

def main():
     usage = 'usage: extractor.py [options] username password'
     aparser = OptionParser(usage, version="visor 0.9.6")
     aparser.add_option('-n', '--net', action='store_true', default=False, dest='net', help='Fetches the data from the net.')
     aparser.add_option('-s', '--serialize', action='store_true', default=False, dest='serialize', help='Serializes the net fetched data.')
     aparser.add_option('-f', '--serialize_from', default='extractor_data.o', dest='fromFile', help='Defines the name of file where the serialized data will be recovered from.')
     aparser.add_option('-t', '--serialize_to', default='extractor_data.o', dest='toFile', help='Defines the name of file where the data will be serialized to.')
     
     (options, args) = aparser.parse_args()
     if len(args) != 2:
          aparser.error('Incorrect usage')
          sys.exit(0)

     df = dataFetcher()
     if options.net:
          df.fetchNetData(sys.argv[1], sys.argv[2])
     else:
          df.fetchSerialized(options.fromFile)
     if options.serialize:
          df.serialize(options.toFile)
     
     trRed = reduce(traceProcess, df.data())
     print etree.tostring(trRed.toXml(), pretty_print = True)

if __name__ == "__main__":
     sys.exit(main())
