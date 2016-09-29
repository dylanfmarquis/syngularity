import os
import time
import pyinotify
import sys
import ConfigParser
from stat import *
from time import strftime as date

class Logging(object):
    def __init__(self):
        self.log = self.open()

    def open(self):
        config = ConfigParser.RawConfigParser()
        config.read('../conf/syngularity.conf')
        log = open(config.get('general','log_path'), 'a')
        return log

    def level_case(self, lvl):
        if lvl == 'e':
                return 'ERROR'
        if lvl == 'i':
                return 'INFO'

    def write(self, level, msg):
        self.log.write("[{0}] [{1}]: {2}\n"\
                .format(date('%Y-%m-%d %H:%M:%S'), self.level_case(level), msg))
        self.log.flush()
        os.fsync(self.log)
        return 0

class inspect(object):
    def delta(term):
        """
        if term - mtime stat:
            check md5
            if different:
                check w/ other sources
                if different:
                    sync
        """

class scan(object):
    def __init__(self):
        config = ConfigParser.RawConfigParser()
        config.read('../conf/syngularity.conf')
        with open(config.get('general','termination_file'), 'r') as f:
            term = f.read()

    def init(self, top):
        inspect = inspect()
        try:
		    Walk().walktree(top, term)
        except Exception as e:
            Logging().write('e',\
                'Rectification scan could not be performed{0}'.format(e))
        #Kill Thread
        sys.exit(0)

class Walk(object):

    def walktree(self, top, callback):
        '''recursively descend the directory tree rooted at top'''
        for f in os.listdir(top):
            pathname = os.path.join(top, f)
            mode = os.stat(pathname).st_mode
            if S_ISDIR(mode):
                # It's a directory, recurse into it
                self.walktree(pathname, callback)
            elif S_ISREG(mode):
                # It's a file, call the callback function
                callback(l_compiled,pathname)
            else:
                # Unknown file type, print a message
                pass

def daemonize():
    try:
        pid = os.fork()
        if pid > 0:
            #Exit first parent
            sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        #Change working directory, change group leader
        os.chdir("/")
        os.setsid()
        os.umask(0)

        #Second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError, e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        #Redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = file('/dev/null', 'r')
        so = file('/dev/null', 'a+')
        se = file('/dev/null', 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        #Delete stale PID file
    try:
        os.remove('/var/run/syngularity.pid')
    except:
        pass
        #Create PID file
        pid = str(os.getpid())
        file('/var/run/syngularity.pid','w+').write("%s\n" % pid)
    return 0
