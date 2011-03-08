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
import cherrypy
import sys
from wisemlModules import *
from lxml import etree
from optparse import OptionParser

class Raw():
     @cherrypy.expose
     def index(self):
          cherrypy.response.headers['Content-Type']= 'text/plain; charset=UTF-8'
          cherrypy.response.headers['Content-Disposition'] = 'attachment; filename="barcelonatech_raw.txt"'
          def content():
               for l in self.obj:
                    yield l
          return content()
     index._cp_config = {'response.stream': True}
     
     def setRawObject(self, o):
          self.obj = o
          
class HumanReadable():
     @cherrypy.expose
     def index(self):
          cherrypy.response.headers['Content-Type']= 'text/plain'
          cherrypy.response.headers['Content-Disposition'] = 'attachment; filename="barcelonatech_human.txt"'
          return self.out
     def setRawObject(self, o):
          self.out = str(o)

class WiseML():
     @cherrypy.expose
     def index(self):
          cherrypy.response.headers['Content-Type']= 'text/xml'
          cherrypy.response.headers['Content-Disposition'] = 'attachment; filename="barcelonatech.wiseml"'

          def content():
               yield '<?xml version="1.0" encoding="UTF-8"?>\n'
               yield self.out
          return content()
     def setRawObject(self, o):
          self.out = etree.tostring(o.toXml(), pretty_print = True)

class WiseMLServer:
     raw = Raw()
     human = HumanReadable()
     wiseml = WiseML()
     def __init__(self, df):
          print >> sys.stderr, 'Retrieving the data...',
          data = df.data()
          print >> sys.stderr,'Done.'
          WiseMLServer.raw.setRawObject(data)
          print >> sys.stderr,'Converting the data to experiment and traces...',
          trRed = reduce(traceProcess, data)
          print >> sys.stderr,'Done.'
          WiseMLServer.human.setRawObject(trRed)
          WiseMLServer.wiseml.setRawObject(trRed)
          print >> sys.stderr,'Starting the server.'
     @cherrypy.expose
     def index(self):
          indexForm = """<?xml version="1.0" encoding="UTF-8"?> 
          <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
             "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd"> 
             <!--
             Copyright 2010 BarcelonaTech
             Author: Antoni Segura
             --> 
             <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en"> 
                 <head> 
                     <title>Sensor data in BarcelonaTech library</title> 
                     </head> 
                      
                      <body> 
                      <b>Solar and environmental data in Barcelona</b><br/> 
                      <br/> 
                      Get data in the following format:<br/> 
                      <a href="raw">Raw</a><br/> 
                      <a href="human">Human readable</a><br/> 
                      <a href="wiseml">WiseML</a><br/> 
                      <br/> 
                      <form action="intervals"> 
                      <p> 
                      Generate file on following intervals:<br/> 
                      <label for="start">Start date (YYYY-MM-DD): </label> 
                      <input type="text" id="start" name="start"/><br/> 
                      <label for="end">End date (YYYY-MM-DD): </label> 
                      <input type="text" id="end" name="end"/><br/> 
                      <input type="submit"/><input type="reset"/> 
                      </p> 
                      </form> 
                      </body> 
                      </html>"""
          return indexForm

def main():
     usage = 'usage: extractor.py [options] username password'
     aparser = OptionParser(usage, version="visor 0.9.6")
     aparser.add_option('-n', '--net', action='store_true', default=False, dest='net', help='Fetches the data from the net.')
     aparser.add_option('-s', '--serialize', action='store_true', default=False, dest='serialize', help='Serializes the net fetched data. Doesn\'t start the web server.')
     aparser.add_option('-f', '--serialize_from', default='extractor_data.o', dest='fromFile', help='Defines the name of file where the serialized data will be recovered from.')
     aparser.add_option('-t', '--serialize_to', default='extractor_data.o', dest='toFile', help='Defines the name of file where the data will be serialized to.')
     
     (options, args) = aparser.parse_args()
     if options.net and len(args) != 2:
          aparser.error('Incorrect usage')
          sys.exit(0)

     df = dataFetcher()
     if options.net:
          df.fetchNetData(args[0], args[1])
     else:
          df.fetchSerialized(options.fromFile)
     if options.serialize:
          df.serialize(options.toFile)
     else:
          cherrypy.quickstart(WiseMLServer(df))

if __name__ == "__main__":
     sys.exit(main())
