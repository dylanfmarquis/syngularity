#import sys
#sys.path.append('../lib')
import os
import time
import pyinotify
import sys
import datetime
import ConfigParser
from libmsgq import *
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

class sync(object):
    config = ConfigParser.RawConfigParser()
    config.read('../conf/syngularity.conf')
    args = '{0} {1} {2}'.format(config.get('sync','rsync_binary'), '-ltrp', '--delete')

class delta(object):
    def __init__(self,top, csn):
        self.top = top
        self.csn = csn
        self.array = []

    def scan(self):
        self.walktree(self.top,self.inspect)
        return self.array

    def inspect(self, path):
        if os.stat(path) > self.csn:
            self.array.append(path)


    def walktree(self, top, callback):
        for f in os.listdir(top):
            pathname = os.path.join(top, f)
            mode = os.stat(pathname).st_mode
            if S_ISDIR(mode):
                self.walktree(pathname, callback)
            elif S_ISREG(mode):
                callback(pathname)
            else:
                pass

class peer_exec(object):

    def __init__(self, peers):
        self.handles = self.open_handles(peers)


    def open_handles(self, peers):
        d = {}
        for peer in peers:
            peer = peer.split(':')
            d[peer[0]] = client(peer[0], peer[1])
        return d

    def send(self, msg):
        for handle in self.handles:
            self.handles[handle].send(msg)

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
