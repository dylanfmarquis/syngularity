import sys
import zmq
import socket

class client(object):

    def __init__(self, host, port):
        self.sock = self.init_socket(host, port)
        self.host = host
        self.port = port

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
        r = self.send('REQ|HEALCHK||{0}'.format(self.host))
        return r

    def peer(self):
        r = self.send('REQ|PEER||{0}'.format(self.host))
        return r

    def state_transfer(self):
        r = self.send('REQ|STATE_XFER||{0}'.format(self.host))
        return r.split('|')

def mq_server(port, callback):
    context = zmq.Context()
    sock = context.socket(zmq.REP)
    sock.bind("tcp://*:{0}".format(port))
    while True:
        message = sock.recv()
        ret = callback(message)
        sock.send(ret)

def repbuild(resp, payload):
    return ('REP|{0}|{1}|{2}').format(resp, payload, socket.gethostbyname(socket.gethostname()))

def ServerReqHandler(msg):
    req = msg.split('|')
    if 'HEALCHK' in req[1]:
        return repbuild('HEALCHK', health)
    if 'PEER' in req[1]:
        return repbuild('PEER', 0)
    if 'STATE_XFER' in req[1]:
        #State Transfer
        return repbuild('STATE_XFER', 0)
