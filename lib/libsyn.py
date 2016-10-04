#import sys
#sys.path.append('../lib')
import os
import time
import pyinotify
import sys
import datetime
import subprocess
import ConfigParser
from libmsgq import *
from stat import *
from time import strftime as date
from subprocess import PIPE
from subprocess import Popen as popen

class logging(object):
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
        if lvl == 'd':
                return 'DEBUG'

    def write(self, level, msg):
        self.log.write("[{0}] [{1}]: {2}\n"\
                .format(date('%Y-%m-%d %H:%M:%S'), self.level_case(level), msg))
        self.log.flush()
        os.fsync(self.log)
        return 0

class sync(object):
    def __init__(self):
        config = ConfigParser.RawConfigParser()
        config.read('../conf/syngularity.conf')
        self.lvl = config.get('general','log_level')
        if self.lvl is 'DEBUG':
            self.log = logging()
        self.user = config.get('sync','user')
        self.target = config.get('sync','target_path')
        self.rsync_bin = config.get('sync','rsync_binary')
        self.cmd = self.rsync_config()

    def rsync_config(self):
        config = ConfigParser.RawConfigParser()
        args = '{0} {1} {2}'.format(self.rsync_bin, '-ltrp', '--delete')
        if configchk('sync','exclude') is not None:
            args += ' --exclude {0}'.format(config.get('sync','exclude'))
        return args

    def state_transfer(self, recipient):
        logging().write('i','State transfer requested by {0}'.format(recipient))
        #health = 3
        p = subprocess.Popen('{0} {1} {2}@{3}:{1}'\
                .format(self.cmd, self.target, self.user, recipient))
        p.communicate()
        #health = 0
        logging().write('i','State transfer with {0} complete'.format(recipient))
        return 0

    def file_sync(self, path, recipient):
        try:
            p = subprocess.Popen('{0} {1} {2}@{3}:{1}'\
                    .format(self.cmd, path, self.user, recipient),shell=True)
            if self.lvl is 'DEBUG':
                self.log.write('d', '{0} - Sync - {1}'.format(recipient, path))
        except:
            logging().write('e', '{0} - Failed - {1}'.format(recipient, path))

    def push(self, path, peers):
        for peer in peers:
            self.file_sync(path, peer.split(':')[0])

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

def configchk(section, config):
    config = ConfigParser.RawConfigParser()
    config.read('../conf/syngularity.conf')
    try:
        return config.get(section,config)
    except:
        return None

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
