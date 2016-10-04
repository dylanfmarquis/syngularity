import sys
sys.path.append('../lib')
import asyncore
import pyinotify
import warnings
from libsyn import *
from libmsgq import *
from multiprocessing import Process
import hashlib
import xattr
import os
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

    #ret = daemonize()
    #if ret is not 0:
    #    print 'exit: ' + ret
    #    sys.exit()

    config = ConfigParser.RawConfigParser()
    config.read('../conf/syngularity.conf')
    bootstrap = config.get('general','boostrap_mode')
    target = config.get('sync','target_path')
    freq = config.get('sync','frequency')
    peers = config.get('general','peers').split(',')

    peer = peer_exec(peers)

    if bootstrap is 'no':
        for peer in peers:
            p = peer.split(':')
            r = client(p[0], p[1]).state_transfer()
            if r[3] is '0':
                break

    l = Process(target=mq_server, args=('5555', ServerReqHandler))
    l.daemon = True
    l.start()

    sync = sync()

    wm = pyinotify.WatchManager()
    mask = pyinotify.IN_MODIFY | pyinotify.IN_CREATE | pyinotify.IN_DELETE

    class EventHandler(pyinotify.ProcessEvent):
        def process_IN_CREATE(self, event):
            sync.push(event.pathname, peers)

        def process_IN_MODIFY(self, event):
            sync.push(event.pathname, peers)

        def process_IN_DELETE(self, event):
            sync.push(event.pathname, peers)

    notifier = pyinotify.AsyncNotifier(wm, EventHandler(), read_freq=freq)
    wdd = wm.add_watch(target, mask, rec=True, auto_add=True)

    asyncore.loop()
