#!/usr/bin/env python
"""
This file is part of WSN-WiseML.

WSN-WiseML is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

WSN-WiseML is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with WSN-WiseML.  If not, see <http://www.gnu.org/licenses/>.
"""
import sys, os, datetime, cherrypy, logging
from wisemlModules import dataFetcher, traceProcess, log, experiment
from lxml import etree
from optparse import OptionParser

class Raw():
    def __init__(self):
        self.inMaintenance = False

    @cherrypy.expose
    def index(self):
        if self.inMaintenance == True:
            return Maintenance.maintenancePage()
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
    def __init__(self):
        self.inMaintenance = False

    @cherrypy.expose
    def index(self):
        if self.inMaintenance == True:
            return Maintenance.maintenancePage()
        cherrypy.response.headers['Content-Type']= 'text/plain'
        cherrypy.response.headers['Content-Disposition'] = 'attachment; filename="barcelonatech_human.txt"'
        return self.out

    index._cp_config = {'tools.encode.on': True, 'tools.encode.encoding': 'utf-8'}

    def setRawObject(self, o):
        self.out = unicode(o)

class WiseML():
    def __init__(self):
	self.inMaintenance = False

    @cherrypy.expose
    def index(self):
        if self.inMaintenance == True:
            return Maintenance.maintenancePage()
        cherrypy.response.headers['Content-Type']= 'text/xml'
        cherrypy.response.headers['Content-Disposition'] = 'attachment; filename="barcelonatech.wiseml"'

        def content():
            yield '<?xml version="1.0" encoding="UTF-8"?>\n'
            yield self.out
        return content()
    def setRawObject(self, o):
        self.out = etree.tostring(o.toXml(), pretty_print = True, encoding="UTF-8")

class Intervals():
    def __init__(self):
        self.inMaintenance = False

    @cherrypy.expose
    def index(self, start = None, end = None, interval_type = None):
        if self.inMaintenance == True:
            return Maintenance.maintenancePage()
        sl = map(lambda x: int(x), start.split('-'))
        el = map(lambda x: int(x), end.split('-'))
        st = datetime.datetime(sl[0], sl[1], sl[2])
        et = datetime.datetime(el[0], el[1], el[2])
        if not interval_type or interval_type == 'wiseml':
            try:
                out = etree.tostring(self.obj.toXml(st, et), pretty_print = True, encoding="UTF-8")
                cherrypy.response.headers['Content-Type']= 'text/xml'
                cherrypy.response.headers['Content-Disposition'] = 'attachment; filename="barcelonatech.wiseml"'
                def wiseContent():
                    yield '<?xml version="1.0" encoding="UTF-8"?>\n'
                    yield out
            except ValueError:
                cherrypy.response.headers['Content-Type']= 'text/plain'
                def wiseContent():
                    yield 'No data for the selected time range'
            return wiseContent()
        else:
            try:
                out = self.obj.toPng(st, et, interval_type)
                cherrypy.response.headers['Content-Type']= 'image/png'
                cherrypy.response.headers['Content-Disposition'] = 'attachment; filename="barcelonatech_'+interval_type+'.png"'
            except ValueError:
                cherrypy.response.headers['Content-Type']= 'text/plain'
                out = "No data for the selected time range"
            return out

    def setRawObject(self, o):
        self.obj = o

class Maintenance():
    @staticmethod
    def maintenancePage():
        maintenancePage = """<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
           "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
           <!--
           Copyright 2010 BarcelonaTech
           Author: Antoni Segura
           -->
           <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
              <head>
                 <title>Sensor data in BarcelonaTech library - Maintenance</title>
	           <link rel="icon" type="image/x-icon" href="favicon.ico">
                 </head>

                  <body>
                  <b>Solar and environmental data in Barcelona</b><br/>
                  <br/>
                  <p>The server is ongoing a scheduled maintenance. Please, try again in 5-10 minutes.</p>
                  </form>
                  </body>
                  </html>"""
        return maintenancePage

class WiseMLServer:
    raw = Raw()
    human = HumanReadable()
    wiseml = WiseML()
    intervals = Intervals()
    def __init__(self, df, logger = None):
        self.df = df
        self.logger = logger
        self.loadData(WiseMLServer.raw, WiseMLServer.human, WiseMLServer.wiseml, WiseMLServer.intervals)
        log(logger, logging.INFO, 'Registering sigusr1 signal to update.')
        cherrypy.engine.signal_handler.handlers['SIGUSR1'] = self.update
        log(logger, logging.INFO, 'Starting the server.')

    def loadData(self, raw, human, wiseml, intervals):
        log(self.logger, logging.INFO, 'Retrieving the data.')
        self.data = self.df.data()
        log(self.logger, logging.INFO, 'Converting the data to experiment and traces.')
        self.trRed = reduce(traceProcess, self.data)
        log(self.logger, logging.INFO, 'Passing the experiment and traces to the webapps.')
        raw.setRawObject(self.data)
        human.setRawObject(self.trRed)
        wiseml.setRawObject(self.trRed)
        intervals.setRawObject(self.trRed)

    def update(self):
        log(self.logger, logging.INFO, 'Received signal SIGUSR1, updating.')
        log(self.logger, logging.INFO, 'Setting the maintenance pages.')
        WiseMLServer.raw.inMaintenance = True
        WiseMLServer.human.inMaintenance = True
        WiseMLServer.wiseml.inMaintenance = True
        WiseMLServer.intervals.inMaintenance = True
        log(self.logger, logging.INFO, 'Fetching data from the net.')
        self.df.fetchNetData(weekOrYear = False)
        self.df.serialize()
        self.loadData(WiseMLServer.raw, WiseMLServer.human, WiseMLServer.wiseml, WiseMLServer.intervals)
        log(self.logger, logging.INFO, 'Restoring functional pages.')
        WiseMLServer.raw.inMaintenance = False
        WiseMLServer.human.inMaintenance = False
        WiseMLServer.wiseml.inMaintenance = False
        WiseMLServer.intervals.inMaintenance = False
        log(self.logger, logging.INFO, 'Update process finished.')

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
	           <link rel="icon" type="image/x-icon" href="favicon.ico">
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
                  Generate a WiseML file or a graph for the following interval:<br/>
                  <input type="radio" name="interval_type" value="wiseml" default> WiseML<br>
                  <input type="radio" name="interval_type" value="""+'"'+experiment.TEMP+'"'+"""> Temperature<br>
                  <input type="radio" name="interval_type" value="""+'"'+experiment.LUM+'"'+"""> Luminosity<br>
                  <input type="radio" name="interval_type" value="""+'"'+experiment.HUM+'"'+"""> Humidity<br>
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
    aparser.add_option('-p', '--port', default='8080', dest='port', help='Defines the port in which to start up the server.')

    (options, args) = aparser.parse_args()
    if len(args) != 2:
        aparser.error('Incorrect usage')
        sys.exit(0)

    logger = logging.getLogger('wiseserver')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)
    logger.addHandler(console)

    df = dataFetcher(args[0], args[1], serializedFile = options.toFile, logger = logger)
    if options.net:
        log(logger, logging.INFO, 'Fetching data from the net.')
        df.fetchNetData()
    else:
        log(logger, logging.INFO, 'Fetching data from a serialized file.')
        df.fetchSerialized(options.fromFile)
    if options.serialize:
        df.serialize(options.toFile)
    else:
        cherrypy.log.access_log.addHandler(console)
        cherrypy.log.error_log.addHandler(console)
        cherrypy.log.screen = False
        cherrypy.config.update({'server.socket_port':int(options.port), 'server.socket_host': '0.0.0.0', })
        conf = {'/favicon.ico':{'tools.staticfile.on': True, 'tools.staticfile.filename': os.path.join(os.getcwd(), 'favicon.ico')}}
        cherrypy.quickstart(WiseMLServer(df, logger), '/', conf)

if __name__ == "__main__":
    sys.exit(main())
