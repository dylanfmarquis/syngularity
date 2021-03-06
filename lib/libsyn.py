import os
import time
import pyinotify
import sys
import datetime
import threading
import subprocess
import hashlib
import ConfigParser
from libmsgq import *
from stat import *
from pwd import getpwnam
from time import strftime as date
from subprocess import PIPE
from subprocess import Popen as popen
from multiprocessing import Process


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

class keys(object):
    def __init__(self):
        keys = self.keypair()
        self.private = keys[0]
        self.public = keys[1]

    def keypair(self):
        keys = []
        if os.path.isfile('../var/keys/id_rsa')\
                and os.path.isfile('../var/keys/id_rsa.pub'):
            with open ('../var/keys/id_rsa', 'r') as priv:
                keys.append(priv.read())
            with open('../var/keys/id_rsa.pub', 'r') as pub:
                keys.append(pub.read())
        else:
            config = ConfigParser.RawConfigParser()
            config.read('../conf/syngularity.conf')
            ssh_bin = config.get('general','ssh-keygen_bin')
            p = subprocess.Popen("{0} -f ../var/keys/id_rsa -t rsa -N ''"
                    .format(ssh_bin), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            p.communicate()
            os.chmod('../var/keys/id_rsa', 0400)
            os.chmod('../var/keys/id_rsa.pub',  0400)
            with open('../var/keys/id_rsa', 'r') as f:
                keys.append(f.read())
            with open('../var/keys/id_rsa.pub', 'r') as f:
                keys.append(f.read())
        return keys

    def store(self, host, key):
        id = hashlib.md5(host).hexdigest()
        with open('../var/keys/{0}'.format(id), 'w') as f:
            f.write(key)
        config = ConfigParser.RawConfigParser()
        config.read('../conf/syngularity.conf')
        user = config.get('sync','user')
        home = os.path.expanduser('~{0}'.format(user))
        auth_keys_path = '{0}/.ssh/authorized_keys'.format(home)

        if not os.path.isfile(auth_keys_path):
            open(auth_keys_path, 'a').close()
            os.chmod(auth_keys_path, 0600)
            try:
                os.chown(auth_keys_path, getpwnam(user).pw_uid, getpwnam(user).pw_gid)
            except:
                os.chown(auth_keys_path, getpwnam(user).pw_uid, 0)

        with open(auth_keys_path, 'ab+') as f:
            contents = f.readlines()
            for line in contents:
                if key in line:
                    return 0
            f.write(key)

        os.chmod(auth_keys_path, 0600)
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
        args = '{0} {1} {2}'.format(self.rsync_bin,\
                "-ltrRp -e 'ssh -o StrictHostKeyChecking=no -i {0}' "\
                .format('../var/keys/id_rsa'), '--delete')
        if configchk('sync','exclude') is not None:
            args += ' --exclude {0}'.format(config.get('sync','exclude'))
        return args

    def state_transfer(self, recipient):
        logging().write('i','State transfer requested by {0}'.format(recipient))
        health = 3
        p = subprocess.Popen('{0} {1} {2}@{3}:/'\
                .format(self.cmd, self.target, self.user, recipient), shell=True)
        p.communicate()
        health = 0
        logging().write('i','State transfer with {0} complete'.format(recipient))

    def file_sync(self, path, recipient):
        try:
            p = subprocess.Popen('{0} {1} {2}@{3}:/'\
                    .format(self.cmd, path, self.user, recipient), shell=True)
            p.communicate()
            if self.lvl is 'DEBUG':
                self.log.write('d', '{0} - Sync - {1}'.format(recipient, path))
        except:
            logging().write('e', '{0} - Sync Failed - {1}'.format(recipient, path))

    def push(self, path, peers):
        for peer in peers:
            self.file_sync(path, peer.split(':')[0])

    def file_del(self, path, recipient):
       try:
            p = subprocess.Popen('ssh -o StrictHostKeyChecking=no -i {0} {1}@{2} "rm -rf {3}"'\
                    .format('../var/keys/id_rsa', self.user, recipient, path),shell=True)
            p.communicate()
            if self.lvl is 'DEBUG':
                self.log.write('d', '{0} - Delete - {1}'.format(recipient, path))
       except:
            logging().write('e', '{0} - Delete Failed - {1}'.format(recipient, path))

    def delete(self, path, peers):
        for peer in peers:
            self.file_del(path, peer.split(':')[0])


def worker(q, peers, sync):
    while True:
        while not q.empty():
            job = q.get(block=True)
            try:
                if job[0] is 0:
                    sync.push(job[1], peers)
                else:
                    sync.delete(job[1], peers)
                q.task_done()
            except:
                continue

def worker_throttled(q, peers, sync):
    i = 0
    while True:
        while i < 5:
            while not q.empty():
                job = q.get(block=True)
                try:
                    if job[0] is 0:
                        sync.push(job[1], peers)
                    else:
                        sync.delete(job[1], peers)
                    q.task_done()
                except:
                    continue
            i += 1
        time.sleep(0.1)
        i=0

def worker(q, peers, sync):
    while True:
        while not q.empty():
            job = q.get(block=True)
            try:
                if job[0] is 0:
                    sync.push(job[1], peers)
                else:
                    sync.delete(job[1], peers)
                q.task_done()
            except:
                continue

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

def mkdir_p(dir):
    try:
        os.stat(dir)
    except:
        os.mkdir(dir)

def state_request(peers, log):
    for peer in peers:
        p = peer.split(':')
        r = client(p[0], p[1]).state_transfer()
        if r[3] is '0':
            return 0
    else:
        log.write('i', 'Node is in bootstrap mode. Skipping state transfer.')

def hidden_file_filter(path):
    array = path.split('/')
    if array[len(array)-1][0] is '.':
        return True
    return False

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
