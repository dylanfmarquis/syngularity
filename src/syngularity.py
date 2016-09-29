import sys
sys.path.append('../lib')
import asyncore
import pyinotify
import warnings
from libsyn import *
from multiprocessing import Process
import hashlib
import xattr

def insertHash(file):
    try:
        md = hashlib.md5()
        with open(file, 'rb') as f:
            buf = f.read()
            md.update(buf)
            xattr.set(f, "md5", md.hexdigest(), namespace=xattr.NS_USER)
    except:
         pass

if __name__ == "__main__":

   ret = daemonize()
   if ret is not 0:
       print 'exit: ' + ret
       sys.exit()

    config = ConfigParser.RawConfigParser()
    config.read('../conf/syngularity.conf')
    target = config.get('general','target_path')
    freq = config.get('sync','frequency')

    scanner = scan()

    p = Process(target=scanner.rectify, args=[target])
    p.daemon = True
    p.start()

    wm = pyinotify.WatchManager()
    mask = pyinotify.IN_MODIFY | pyinotify.IN_CREATE | pyinotify.IN_DELETE

    class EventHandler(pyinotify.ProcessEvent):
        def process_IN_CREATE(self, event):
            insertHash(event.pathname)
            print event.pathname

        def process_IN_MODIFY(self, event):
            insertHash(event.pathname)
            print event.pathname

        def process_IN_DELETE(self, event):
            print event.pathname + " DELETE"

    notifier = pyinotify.AsyncNotifier(wm, EventHandler(), read_freq=freq)
    wdd = wm.add_watch(target, mask, rec=True, auto_add=True)

    asyncore.loop()
