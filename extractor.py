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
from wisemlModules import *
from lxml import etree
from optparse import OptionParser

def main():
     usage = 'usage: extractor.py [options] username password'
     aparser = OptionParser(usage, version="visor 0.9.6")
     aparser.add_option('-n', '--net', action='store_true', default=False, dest='net', help='Fetches the data from the net.')
     aparser.add_option('-s', '--serialize', action='store_true', default=False, dest='serialize', help='Serializes the net fetched data.')
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
          try:
               df.fetchSerialized(options.fromFile)
          except:
               sys.exit(-1)
     if options.serialize:
          df.serialize(options.toFile)
     else:
          trRed = reduce(traceProcess, df.data())
          print etree.tostring(trRed.toXml(), pretty_print = True)

if __name__ == "__main__":
     sys.exit(main())
