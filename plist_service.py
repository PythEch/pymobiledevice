import sys
import time

import os
import plistlib
import struct
from re import sub
from usbmux import usbmux
from util.bplist import BPlistReader


class PlistService(object):
    def __init__(self, port, udid=None):
        self.port = port
        self.connect(udid)

    def connect(self, udid=None):
        mux = usbmux.USBMux()
        mux.process(5.0)
        dev = None
        try:
            while not mux.devices:
                print "Waiting for iOS device: %s" % udid
                time.sleep(5)
        except KeyboardInterrupt:
            sys.exit(0)
        while not dev and mux.devices:
            #mux.process(1.0)
            if udid:
                for d in mux.devices:
                    if d.serial == udid:
                        dev = d
                        print "Connecting to device: " + dev.serial
            else:
                dev = mux.devices[0]
                print "Connecting to device: " + dev.serial

        #
        #self.udid = dev.serial ###
        try:
            self.s = mux.connect(dev, self.port)
        except:
            raise Exception("Connection to device port %d failed" % self.port)
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
            payload = sub('[^\w<>\/ \-_0-9\"\'\\=\.\?\!\+]+', '', payload.decode('utf-8')).encode('utf-8')
            return plistlib.readPlistFromString(payload)
        else:
            raise Exception("recvPlist invalid data : %s" % payload[:100].encode("hex"))

    def sendPlist(self, d):
        payload = plistlib.writePlistToString(d)
        #print '>>>>',payload
        l = struct.pack(">L", len(payload))
        self.send(l + payload)

    def ssl_start(self, keyfile):
        if os._name == 'nt':
            self.s = usbmux.SSLSocket(self.s.sock._sock._get_jsocket(), keyfile)
        else:
            self.s = usbmux.SSLSocket(self.s.sock, keyfile)
