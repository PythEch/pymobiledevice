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

import time
import struct
from pymobiledevice.lockdown import LockdownClient

LINKTYPE_ETHERNET = 1
LINKTYPE_RAW      = 101

class PcapOut(object):
    def __init__(self, filename, lockdown=None):
        if lockdown:
            self.lockdown = lockdown
        else:
            self.lockdown = LockdownClient()

        self.service = self.lockdown.startService("com.apple.pcapd")

        self.f = open(filename, "wb")
        self.f.write(struct.pack("<LHHLLLL", 0xa1b2c3d4, 2, 4, 0, 0, 65535, LINKTYPE_ETHERNET))

        self.stop = False # use this to stop capturePackets() remotely

    def __del__(self):
        self.f.close()

    def writePacket(self, packet):
        t = time.time()
        #TODO check milisecond conversion
        pkthdr = struct.pack("<LLLL", int(t), int(t*1000000 % 1000000), len(packet), len(packet))
        data = pkthdr + packet
        self.f.write(data)
        self.f.flush()
        return True

    def capturePackets(self):
        while not self.stop:
                d = self.service.recvPlist()
                if not d:
                    break
                data = d.data
                hdrsize, xxx, packet_size = struct.unpack(">LBL", data[:9])
                flags1, flags2, offset_to_ip_data, zero = struct.unpack(">LLLL", data[9:0x19])
                assert hdrsize >= 0x19
                interfacetype = data[0x19:hdrsize].strip("\x00")
                t = time.time()
                print interfacetype, packet_size, t
                packet = data[hdrsize:]
                assert packet_size == len(packet)
                if offset_to_ip_data == 0:
                    #add fake ethernet header for pdp packets
                    packet = "\xBE\xEF" * 6 + "\x08\x00" + packet
                if not self.writePacket(packet):
                    break

if __name__ == "__main__":
    PcapOut("test.pcap").capturePackets()

