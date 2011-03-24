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
import urllib2, sys, urllib, re, pickle, datetime, logging
from cookielib import CookieJar
from lxml import etree
from operator import attrgetter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

class trace:
    """ A sensor network trace. Collects trace data and allows its
    conversion to xml. """
    #: Memoization dictionary for the getTime method.
    times = dict()
    #: A compiled regular expression that matches Date hour:min nodeId nodeName traceId readingType* value
    pattern = re.compile( '(.*?)/(.*?)/(.*?) (.*?):(.*?),(.*?),(.*?),(.*?),(.*?),"(.*?),(.*?)"' )
    #: Returns a regular expression search object that matches pattern.
    search = pattern.search

    @classmethod
    def getTime(cls, tup):
        """Returns and memoizes a datetime object from an ordered tuple.

        Keyword arguments:
        tup -- A tuple containing [year, [month, [day, [hour, [minute]]]]].
        """
        try:
            return cls.times[tup]
        except KeyError:
            t = datetime.datetime(*tup)
            cls.times[tup] = t
            return t

    def __init__(self, rhs):
        """Form a trace object.

        Keyword arguments:
        rhs -- a trace object or a compatible string.
        """
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
            self.nodeId = s.group(6).decode('utf8')
            self.name = s.group(7).decode('utf8')
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
        """Consolidates the data of lhs and rhs.

        Keyword arguments:
        lhs -- Left hand side operator, a trace.
        rhs -- Right hand side operator, a trace.
        """
        if rhs.temp is not None:
            lhs.temp = rhs.temp
        if rhs.hum is not None:
            lhs.hum = rhs.hum
        if rhs.lum is not None:
            lhs.lum = rhs.lum
        return lhs

    def hash(self):
        """Returns a tuple of the key elements of a trace.  """
        return (self.time, self.nodeId)

    def __eq__(lhs, rhs):
        """ Checks if lhs and rhs are logically equal.

        lhs -- Left hand side operator, a trace.
        rhs -- Right hand side operator, a trace.
        """
        return lhs.nodeId == rhs.nodeId and lhs.time == rhs.time

    def __str__(self):
        """ Returns a string representation of the current trace. """
        return str(unicode(self))

    def __unicode__(self):
        """ Returns an unicode representation of the current trace. """
        return u'('+unicode(self.time)+u':'+self.nodeId+u'_'+self.name+u')->'+unicode(self.temp)+u'C '+unicode(self.hum)+u'% '+unicode(self.lum)+u'LUX'

    def toXml(self):
        """ Returns an etree.Element object representation of the current trace. """
        e = etree.Element('node')
        e.attrib['id'] = 'urn:wisebed:upc:'+self.nodeId
        temp = etree.SubElement(e, 'data')
        temp.attrib['key'] = 'urn:wisebed:upc:node:capability:temperature'
        temp.text = unicode(self.temp)
        hum = etree.SubElement(e, 'data')
        hum.attrib['key'] = 'urn:wisebed:upc:node:capability:humidity'
        hum.text = unicode(self.hum)
        lum = etree.SubElement(e, 'data')
        lum.attrib['key'] = 'urn:wisebed:upc:node:capability:light'
        lum.text = unicode(self.lum)
        return e

class experiment:
    """ A sensor network experiment. Collects data and allows its
    conversion to xml. """
    #: Dictionary with node ids and node names.
    nodes = dict()
    TEMP = 'temp'
    HUM = 'hum'
    LUM = 'lum'

    @classmethod
    def trackNodes(cls, rhs):
        """ Fills the node dictionary with the relevant information of rhs.

        rhs -- A trace.
        """
        cls.nodes[rhs.nodeId] = rhs.name

    def __init__(self):
        """ Initializes an empty experiment."""
        self.traces = dict()

    def __init__(self, rhs):
        """ Initializes an experiment containing rhs.

        rhs --- An experiment or a trace.
        """
        try:
            self.traces = rhs.traces
        except AttributeError:
            self.traces = dict()
            rhs = trace(rhs)
            self+=rhs

    def __add__(lhs, rhs):
        """Adds rhs to the lhs experiment.

        Keyword arguments:
        lhs -- An experiment.
        rhs -- A trace.
        """
        h = rhs.hash()
        try:
            lhs.traces[h] += rhs
        except KeyError:
            lhs.traces[h] = rhs
            experiment.trackNodes(rhs)
        return lhs

    def __contains__(lhs, rhs):
        """Checks if rhs is present in lhs.

        Keyword arguments:
        lhs -- An experiment.
        rhs -- A trace.
        """
        for e in lhs.traces:
            if e == rhs:
                return True
        return False

    def __str__(self):
        """ Returns a string representation of the current experiment. """
        return str(unicode(self))

    def __unicode__(self):
        """ Returns an unicode representation of the current experiment. """
        return u'\n'.join([unicode(t) for t in self.traces.values()])+u'\n\n'

    def generateXmlSetup(self, it, et):
        """ Returns an etree.Element object representation of the current experiment's setup.

        Keyword arguments:
        it --- A Datetime object with the initial time of the experiment.
        et --- A Datetime object with the ending time of the experiment.
        """
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
            progDetail = etree.SubElement(node, 'programDetails')
            progDetail.text = 'Environmental conditions tracking software'
            #nodeType
            nodeType = etree.SubElement(node, 'nodeType')
            nodeType.text = 'dexcell'
            #description
            description = etree.SubElement(node, 'description')
            description.text = experiment.nodes[n]
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

    def toXml(self, start = None, end = None):
        """ Returns an etree.Element object representation of the current experiment."""
        traceList = self._timeSortAndFilter(start, end)
        it = traceList[0].time
        lt = traceList[len(traceList)-1].time
        pd = datetime.timedelta(-1)

        root = etree.Element('wiseml')
        root.attrib['version'] = '1.0'
        root.attrib['xmlns'] = 'http://wisebed.eu/ns/wiseml/1.0'
        root.append(self.generateXmlSetup(it, lt))
        for e in traceList:
            t = e.time-it
            if pd != t:
                ts = etree.Element('timestamp')
                ts.text = unicode(t.seconds)
                root.append(ts)
                pd = t
            root.append(e.toXml())
        return root

    def _timeSortAndFilter(self, start = None, end = None):
        """ Returns a sorted list of traces. """
        traceList = self.traces.values()
        traceList.sort(key=attrgetter('time'), reverse=False)
        if start is not None and end is not None:
            i = 0
            j = 0
            for e in traceList:
                if e.time < start:
                    i += 1
                    j += 1
                elif e.time < end:
                    j += 1
                else:
                    break
            return traceList[i:j]
        return traceList

    def toPng(self, start = None, end = None, kind = LUM):
        traceList = self._timeSortAndFilter(start, end)
        initTime = traceList[0].time
        times = list()
        values = list()
        for e in traceList:
            t = e.time-initTime
            times.append(t.days*24*3600+t.seconds)
            values.append(getattr(e, kind))
            if kind == experiment.TEMP:
                plt.ylabel('Celsius' )
            elif kind == experiment.LUM:
                plt.ylabel('LUX' )
            elif kind == experiment.HUM:
                plt.ylabel('Humidity percentage' )
            else:
                return
        buff = StringIO()
        plt.plot(times, values, 'r-')
        plt.xlabel( 'Time in seconds' )
        plt.grid(True)
        canvas = plt.get_current_fig_manager().canvas
        canvas.draw()
        pil_img = Image.fromstring('RGB', canvas.get_width_height(), canvas.tostring_rgb())
        pil_img.save(buff, 'PNG')
        plt.close()
        return buff.getvalue()


def log(logger, level, text, *pars):
    if logger:
        if level is logging.INFO:
            logger.info(text, *pars)
        else:
            logger.error(text, *pars)
    else:
        if level is logging.INFO:
            sys.stdout.write(text % pars)
        else:
            sys.stderr.write(text % pars)

class dataFetcher:
    """ Fetches the data either from the Internet or an extractor
    serialized file and makes it available for serialization and use."""
    def __init__(self, username = None, password = None, serializedFile = 'list_obj.o', logger = None):
        """ Initializes an empty dataFetcher."""
        self.l = list()
        self.username = username
        self.password = username
        self.filename = serializedFile
        self.logger = logger


    def fetchSerialized(self, filename = None):
        """ Fetch the sensor readings from a serialized file.

        Keyword arguments:
        filename --- The name of the file containing the serialized object readings.
        """
        if filename is None:
            filename = self.filename
        try:
            fl = open(filename, 'rb')
        except IOError:
            log(self.logger, logging.ERROR, 'The file %s was not found. Recommended to serialize a new file.', filename)
            sys.exit(0)
        try:
            log(self.logger, logging.INFO, 'Loading data contained in %s.', filename)
            self.l = pickle.load(fl)
        except:
            log(self.logger, logging.ERROR, 'The file %s is not a extractor object. Recommended to serialize a new file.', filename)
            sys.exit(0)
        fl.close()

    def fetchNetData(self, weekOrYear = True):
        """ Fetch the sensor readings from the internet.

        Keyword arguments:
        username --- The webpage username.
        username --- The webpage password.
        weekOrYear --- True if gathering Yearly data, False for weekly data."""

        url = 'http://meteoroleg.upc.es/dexserver/j_spring_security_check'
        if weekOrYear: #Yearly
            urlTemp = 'http://meteoroleg.upc.es/dexserver/report-results.htm?6578706f7274=1&d-49653-e=1&queryId=83'
            urlHum = 'http://meteoroleg.upc.es/dexserver/report-results.htm?6578706f7274=1&d-49653-e=1&queryId=84'
            urlLum = 'http://meteoroleg.upc.es/dexserver/report-results.htm?6578706f7274=1&d-49653-e=1&queryId=85'
        else: #weekly
            urlTemp = 'http://meteoroleg.upc.es/dexserver/report-results.htm?6578706f7274=1&d-49653-e=1&queryId=87'
            urlHum = 'http://meteoroleg.upc.es/dexserver/report-results.htm?6578706f7274=1&d-49653-e=1&queryId=89'
            urlLum = 'http://meteoroleg.upc.es/dexserver/report-results.htm?6578706f7274=1&d-49653-e=1&queryId=91'
        login = { 'j_username': self.username , 'j_password': self.password }
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
        reqTemp =  urllib2.Request(urlTemp, headers = headers)
        reqHum =  urllib2.Request(urlHum, headers = headers)
        reqLum =  urllib2.Request(urlLum, headers = headers)
        log(self.logger, logging.INFO, 'Fetching temperature data from %s', urlTemp)
        respTemp = opener.open(reqTemp)
        log(self.logger, logging.INFO, 'Fetching humidity data from %s', urlHum)
        respHum = opener.open(reqHum)
        log(self.logger, logging.INFO, 'Fetching luminosity data from %s', urlLum)
        respLum = opener.open(reqLum)
        self.l.extend(respTemp)
        self.l.extend(respHum)
        self.l.extend(respLum)

    def serialize(self, filename = None):
        """ Save the sensor readings to a serialized file.

        Keyword arguments:
        filename --- The name of the file in which to serialize the sensor readings.
        """
        if filename is None:
            filename = self.filename
        try:
            fl = open(filename, 'wb')
        except IOError:
            log(self.logger, logging.ERROR, 'Failed to write to %s', filename)
            sys.exit(0)
        log(self.logger, logging.INFO, 'Serializing fetched data to %s', filename)
        pickle.dump(self.l, fl)
        fl.close()

    def data(self):
        """ Returns the sensor readings data as a list. """
        return self.l

def traceProcess(lhs, rhs):
    """ Creates an experiment and a trace and adds the latter to the former.

    Keyword arguments:
    lhs --- A sensor readings string, a trace or an experiment.
    rhs --- A sensor readings string or a trace.
    """

    return experiment(lhs)+trace(rhs)
