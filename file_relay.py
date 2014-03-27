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

from lockdown import LockdownClient

SRCFILES = """AppleSupport
Network
UserDatabases
CrashReporter
tmp
SystemConfiguration
WiFi
VPN
Caches"""

class FileRelayClient(object):
    def __init__(self, lockdown=None, serviceName="com.apple.mobile.file_relay"):
        if lockdown:
            self.lockdown = lockdown
        else:
            self.lockdown = LockdownClient()

        self.service = self.lockdown.startService(serviceName)
        self.packet_num = 0

    def stop_session(self):
        print "Disconecting..."
        self.service.close()

    def request_sources(self, sources=["UserDatabases"]):
        print "Downloading sources ", sources
        self.service.sendPlist({"Sources":sources})
        res = self.service.recvPlist()
        if res:
            if res.has_key("Status"):
                if res["Status"] == "Acknowledged":
                    z = ""
                    while True:
                        x = self.service.recv()
                        if not x:
                            break
                        z += x
                    return z
        return None

if __name__ == "__main__":
    lockdown = LockdownClient()
    ProductVersion = lockdown.getValue("", "ProductVersion")
    assert ProductVersion[0] >= "4"

    fc = FileRelayClient()
    f = fc.request_sources(SRCFILES.split("\n"))
    #f = fc.request_sources(["SystemConfiguration"])
    if f:
        open("fileRelayTest.gz","wb").write(f)
