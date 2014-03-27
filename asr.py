#
# pymobiledevice - Jython implementation of libimobiledevice
#
# Copyright (C) 2014  Taconut <https://github.com/Triforce1>
# Copyright (C) 2014  PythEch <https://github.com/PythEch>
# Copyright (C) 2013  GotoHack <https://github.com/GotoHack>
#
# pymobiledevice is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pymobiledevice is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with pymobiledevice.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
from pprint import pprint
from progressbar import ProgressBar
from plist_service import PlistService

class ASRClient(object):
    def __init__(self, payloadFile):
        self.s = PlistService(12345)
        self.size = os.path.getsize(payloadFile)
        self.packet_payload_size = 1450
        self.f = open(payloadFile, "rb")

    def initiate(self, msg):
        r = {"Checksum Chunk Size": 131072,
             "FEC Slice Stride": 40,
             "Packet Payload Size": self.packet_payload_size,
             "Packets Per FEC": 25,
             "Payload": {"Port": 1, "Size": self.size},
             "Stream ID": 1,
             "Version": 1
             }
        print "ASR: init"
        self.s.sendPlist(r)

    def handle_oob_request(self, msg):
        length = msg["OOB Length"]
        offset = msg["OOB Offset"]
        print "ASR: OOB request off=%d len=%d" % (offset, length)
        self.f.seek(offset)
        data = self.f.read(length)
        self.s.send_raw(data)

    def send_payload(self, msg):
        self.f.seek(0)
        i = self.size

        print "ASR: sending payload (%d bytes)" % self.size
        pbar = ProgressBar(self.size)
        pbar.start()
        while i < self.size:
            data = self.f.read(self.packet_payload_size)
            self.s.send_raw(data)
            i += len(data)
            pbar.update(i)
        pbar.finish()

    def work_loop(self):
        while True:
            msg = self.s.recvPlist()
            if not msg:
                break
            Command = msg["Command"]
            pprint(msg)

            if Command == "Initiate":
                self.initiate(msg)
            elif Command == "OOBData":
                self.handle_oob_request(msg)
            elif Command == "Payload":
                self.send_payload(msg)

if __name__ == "__main__":
    asr = ASRClient(sys.argv[1])
    asr.work_loop()
