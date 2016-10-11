import sys
import zmq
import socket

class client(object):

    def __init__(self, host, port):
        self.sock = self.init_socket(host, port)
        self.host = host
        self.port = port
        self.origin = socket.gethostbyname(socket.gethostname())

    def init_socket(self, host, port):
        context = zmq.Context()
        sock = context.socket(zmq.REQ)
        sock.connect("tcp://{0}:{1}".format(host, port))
        return sock

    def send(self, msg):
        for i in range(10):
            self.sock.send(msg)
            r = self.sock.recv()
            if 'REP' in r:
                return r
        else:
            return 1

    def health_check(self):
        r = self.send('REQ|HEALCHK||{0}'.format(self.origin))
        return r

    def peer(self, keys):
        r = self.send('REQ|PEER|{0}|{1}'.format(keys.public, self.origin))
        keys.store(self.host, r.split('|')[2])
        return 0

    def state_transfer(self):
        r = self.send('REQ|STATE_XFER||{0}'.format(self.origin))
        return r.split('|')

def mq_server(port, callback, sync, keys, log):
    context = zmq.Context()
    sock = context.socket(zmq.REP)
    sock.bind("tcp://*:{0}".format(port))
    while True:
        message = sock.recv()
        ret = callback(message, sync, keys, log)
        sock.send(ret)

def repbuild(resp, payload):
    return ('REP|{0}|{1}|{2}').format(resp, payload, socket.gethostbyname(socket.gethostname()))

def ServerReqHandler(msg, sync, keys, log):
    req = msg.split('|')
    if 'HEALCHK' in req[1]:
        return repbuild('HEALCHK')

    if 'PEER' in req[1]:
        log.write('i','{0} has made a peer request'.format(req[3]))
        keys.store(req[3], req[2])
        log.write('i','{0} joined with cluster'.format(req[3]))
        return repbuild('PEER', keys.public)

    if 'STATE_XFER' in req[1]:
        sync.state_transfer(req[3])
        return repbuild('STATE_XFER', 0)
