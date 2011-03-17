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

import pwd, sys, time, os, signal, logging, logging.handlers, cherrypy
from wisemlModules import dataFetcher, traceProcess, log
from server import WiseMLServer
from daemon import Daemon

class WiseMLServerDaemon(Daemon):
    def run(self):
        #Set up the logger
        logger = logging.getLogger('wiseserver')
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler = logging.handlers.TimedRotatingFileHandler('wise_daemon.log', 'midnight', backupCount = 15)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        #Fetch the data
        try:
            credFile = open('credentials.txt', 'r')
            usr, passwd = credFile.readline().split(' ')
            credFile.close()
        except IOError:
            sys.exit(0)
        df = dataFetcher(usr, passwd[0:-1], 'extractor_data.o', logger)

        if os.path.exists('extractor_data.o'):
            df.fetchSerialized()
        else:
            df.fetchNetData()
            df.serialize()

        cherrypy.log.access_log.addHandler(handler)
        cherrypy.log.error_log.addHandler(handler)
        cherrypy.log.screen = False
        cherrypy.config.update({'server.socket_port': 8080, 'server.socket_host': '0.0.0.0', })
        conf = {'/favicon.ico':{'tools.staticfile.on': True, 'tools.staticfile.filename': os.path.join(os.getcwd(), 'favicon.ico')}}
        cherrypy.quickstart(WiseMLServer(df, logger), '/', conf)

    def update(self):
        # Try killing the daemon process
        try:
            os.kill(self.getPid(), signal.SIGUSR1)
        except OSError, err:
            print str(err)
            sys.exit(1)

    def dropPrivileges(self):
        user = pwd.getpwnam('celebdor')
        os.setgid(user.pw_gid)
        os.setuid(user.pw_uid)
        os.chdir(os.path.join(pwd.getpwnam('celebdor').pw_dir,'WSN-WiseML'))

if __name__ == "__main__":
    daemon = WiseMLServerDaemon('/tmp/wiseml.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        elif 'update' == sys.argv[1]:
            daemon.update()
        else:
            print "Unknown command"
            sys.exit(2)
            sys.exit(0)
    else:
        print "usage: %s start|stop|restart|update" % sys.argv[0]
        sys.exit(2)
