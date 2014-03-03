from usbmux import usbmux
from util.bplist import BPlistReader
import plistlib
import struct
from pprint import pprint
from re import sub
import socket
from org.apache.commons.ssl import SSLClient, KeyMaterial, TrustMaterial

class PlistService(object):
    def __init__(self, port, udid=None):
        self.port = port
        self.connect(udid)

    def connect(self, udid=None):
        mux = usbmux.USBMux()
        mux.process(1.0)
        dev = None
        #if not mux.devices:
        #print "Waiting for iOS device %s" % str(udid)
        while not dev and mux.devices :
            mux.process(1.0)
            if udid:
                for d in mux.devices:
                    if d.serial == udid:
                        dev = d
                        print "Connecting to device: " + dev.serial
            else:
                dev = mux.devices[0]
                print "Connecting to device: " + dev.serial

        #
        self.udid = dev.serial ###
        try:
            self.s = mux.connect(dev, self.port)
        except:
            raise Exception("Connexion to device port %d failed" % self.port)
        return dev.serial

    def close(self):
        self.s.close()

    def recv(self, len=4096):
        return self.s.recv(len)

    def send(self, data):
        return self.s.send(data)

    def recv_exact(self, l):
        data = ""
        while l > 0:
            d = self.recv(l)
            if not d or len(d) == 0:
                break
            data += d
            l -= len(d)
        return data

    def recv_raw(self):
        l = self.recv(4)
        if not l or len(l) != 4:
            return
        l = struct.unpack(">L", l)[0]
        return self.recv_exact(l)

    def send_raw(self, data):
        return self.send(struct.pack(">L", len(data)) + data)

    def recvPlist(self):
        payload = self.recv_raw()
        #print '<<<<<<<<',payload
        if not payload:
            return
        if payload.startswith("bplist00"):
            return BPlistReader(payload).parse()
        elif payload.startswith("<?xml"):
            #HAX lockdown HardwarePlatform with null bytes
            payload = sub('[^\w<>\/ \-_0-9\"\'\\=\.\?\!\+]+','', payload.decode('utf-8')).encode('utf-8')
            return plistlib.readPlistFromString(payload)
        else:
            raise Exception("recvPlist invalid data : %s" % payload[:100].encode("hex"))

    def sendPlist(self, d):
        payload = plistlib.writePlistToString(d)
        #print '>>>>',payload
        l = struct.pack(">L", len(payload))
        self.send(l + payload)

    def ssl_start(self, keyfile, certfile):
        # = Monkey-Patch! = #
        socket.ssl._make_ssl_socket = self._nycs_socket
        self.keyfile = keyfile # no parameter is used in original socket.py
        #certfile isn't necessary because of TRUST_ALL
        self.s = socket.ssl(self.s)
        #It'd be good if this was default behaviour
        self.s.send = self.s.write
        self.s.recv = self.s.read

    def _nycs_socket(self, jython_socket):
        java_net_socket = jython_socket._get_jsocket()
        host = java_net_socket.getInetAddress().getHostAddress()
        port = java_net_socket.getPort()
        client = SSLClient()
        client.setCheckHostname(False)
        client.setCheckExpiry(False)
        client.setCheckCRL(False)
        client.setKeyMaterial(KeyMaterial(self.keyfile, ""))
        client.setTrustMaterial(TrustMaterial.TRUST_ALL)
        s = client.createSocket(java_net_socket, host, port, 0)
        s.startHandshake()
        return s
