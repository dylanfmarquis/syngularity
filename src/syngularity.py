import sys
sys.path.append('../lib')
import asyncore
import pyinotify
import warnings
from libsyn import *
from libmsgq import *
from multiprocessing import Process
import hashlib
from Queue import *
import os
import re
import calendar
from stat import *

### health of node
# 0 - synchronized and healthy
# 1 - degraded - awaiting state transfer
# 2 - recipient - receiving state transfer
# 3 - donor - transferring state to another node

global health
health = 1

if __name__ == "__main__":

    mkdir_p('../var')
    mkdir_p('../var/log')
    mkdir_p('../var/keys')

    config = ConfigParser.RawConfigParser()
    config.read('../conf/syngularity.conf')
    target = config.get('sync','target_path')
    freq = config.get('sync','frequency')
    peers = config.get('general','peers').split(',')
    log = logging()

    log.write('i', 'Starting Singularity...')

    keys = keys()

    #ret = daemonize()
    #if ret is not 0:
    #    print 'exit: ' + ret
    #    sys.exit()

    sync = sync()

    bootstrap = config.get('general','boostrap_mode')

    #MAKE SURE IT'S RECEIVING UPDATES WHILE ITS STATE TRANSFERRING
    if 'disabled' in bootstrap:
        for peer in peers:
            l = peer.split(':')
            client(l[0],l[1]).peer(keys)
        state_request(peers, log)


    log.write('i', 'Starting MQ server')
    l = Process(target=mq_server, args=('5555', ServerReqHandler, sync, keys, log))
    l.daemon = True
    l.start()

    ext_exclude = re.compile('^.*(.swp|.swpx)$')

    q = Queue()

    log.write('i', 'Starting worker threads')
    for i in range(int(config.get('sync','workers'))):
        t = threading.Thread(target=worker, args=(q, peers, sync))
        t.start()

    log.write('i', 'Enabling inotify event watch')
    wm = pyinotify.WatchManager()
    mask = pyinotify.IN_MOVED_TO | pyinotify.IN_MOVED_FROM | pyinotify.IN_CLOSE_WRITE\
            | pyinotify.IN_CREATE | pyinotify.IN_DELETE

    # USE MASK TO REMOVE PEERS THAT AREN'T UP
    class EventHandler(pyinotify.ProcessEvent):
        def process_IN_CREATE(self, event):
            if ext_exclude.findall(event.pathname):
                pass
            else:
                q.put([0, event.pathname])

        def process_IN_MOVED_TO(self, event):
            if ext_exclude.findall(event.pathname):
                print event.pathname
                pass
            else:
                q.put([0, event.pathname])

        def process_IN_MOVED_FROM(self, event):
            if ext_exclude.findall(event.pathname):
                print event.pathname
                pass
            else:
                q.put([1, event.pathname])

        def process_IN_CLOSE_WRITE(self, event):
            if ext_exclude.findall(event.pathname):
                pass
            else:
                q.put([0, event.pathname])

        def process_IN_DELETE(self, event):
            if ext_exclude.findall(event.pathname):
                pass
            else:
                q.put([1, event.pathname])

    notifier = pyinotify.AsyncNotifier(wm, EventHandler(), read_freq=freq)
    wdd = wm.add_watch(target, mask, rec=True, auto_add=True)

    asyncore.loop()
