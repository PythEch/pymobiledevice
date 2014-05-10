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

import platform
import plistlib
import uuid
from util import readHomeFile, writeHomeFile

from certificate import generateCertificates
from plist_service import PlistService


#we store pairing records and ssl keys in ~/.pymobiledevice
HOMEFOLDER = '.pymobiledevice'

class NotTrustedError(Exception):
    pass

class PairingError(Exception):
    pass

class NotPairedError(Exception):
    pass

class CannotStopSessionError(Exception):
    pass

class StartServiceError(Exception):
    pass

class FatalPairingError(Exception):
    pass

class LockdownClient(object):
    def __init__(self, udid=None):
        self.service = PlistService(62078, udid)
        self.hostID = self.generate_hostID()
        self.paired = False
        self.label = 'pyMobileDevice'
        self.service.sendPlist({
            'Request': 'QueryType'
            })
        response = self.service.recvPlist()
        assert response['Type'] == 'com.apple.mobile.lockdown'

        self.allValues = self.getValue('', '')
        self.udid = self.allValues.get('UniqueDeviceID')
        self.osVersion = self.allValues.get('ProductVersion')
        self.devicePublicKey = self.allValues.get('DevicePublicKey').data

        if not self.validate_pairing():
            self.pair()
            if not self.validate_pairing():
                raise FatalPairingError
        self.paired = True

    def generate_hostID(self):
        hostname = platform.node()
        hostid = uuid.uuid3(uuid.NAMESPACE_DNS, hostname)
        return str(hostid).upper()

    def enter_recovery(self):
        self.service.sendPlist({
            'Request': 'EnterRecovery'
            })
        return self.service.recvPlist()

    def stop_session(self):
        if self.SessionID and self.service:
            self.service.sendPlist({
                'Request': 'StopSession',
                'SessionID': self.SessionID
                })
            self.SessionID = None
            response = self.service.recvPlist()
            if not response or response.get('Result') != 'Success':
                raise CannotStopSessionError
            return response

    def validate_pairing(self):
        record = readHomeFile(HOMEFOLDER, '%s.plist' % self.udid)
        if record:
            pair_record = plistlib.readPlistFromString(record)
            hostCertificate = pair_record['HostCertificate'].data
            hostPrivateKey = pair_record['HostPrivateKey'].data
            print "Found pairing record for device %s" % self.udid
        else:
            print "No pairing record found for device %s" % self.udid
            return False

        self.service.sendPlist({
            'Request': 'ValidatePair',
            'PairRecord': pair_record
            })
        ValidatePair = self.service.recvPlist()

        if not ValidatePair or 'Error' in ValidatePair:
            pair_record = None
            return False

        self.service.sendPlist({
            'Request': 'StartSession',
            'HostID': pair_record.get('HostID', self.hostID)
            })
        StartSession = self.service.recvPlist()
        self.SessionID = StartSession.get('SessionID')

        if StartSession.get('EnableSessionSSL'):
            keyfile = writeHomeFile(HOMEFOLDER, self.udid + "_ssl.txt", hostCertificate + '\n' + hostPrivateKey)
            self.service.start_ssl(keyfile)
            self.allValues = self.getValue('', '')
        return True

    def pair(self):
        print "Creating host key & certificate"
        hostCertificate, hostPrivateKey, deviceCertificate = generateCertificates(self.devicePublicKey)

        pair_record = {'DevicePublicKey': plistlib.Data(self.devicePublicKey),
                       'DeviceCertificate': plistlib.Data(deviceCertificate),
                       'HostCertificate': plistlib.Data(hostCertificate),
                       'HostPrivateKey': plistlib.Data(hostPrivateKey),
                       'HostID': self.hostID,
                       'RootCertificate': plistlib.Data(hostCertificate),
                       'SystemBUID': '30142955-444094379208051516'}

        self.service.sendPlist({
            'Request': 'Pair',
            'PairRecord': pair_record
            })
        Pair = self.service.recvPlist()

        if self.osVersion[0] == '7' and Pair.get('Error') == 'PasswordProtected':
            raise NotTrustedError

        if Pair and Pair.get('Result') == 'Success' or 'EscrowBag' in Pair:
            if 'EscrowBag' in Pair:
                pair_record['EscrowBag'] = Pair['EscrowBag']
            writeHomeFile(HOMEFOLDER, '%s.plist' % self.udid, plistlib.writePlistToString(pair_record))
        else:
            raise PairingError(str(Pair))

    def getValue(self, domain=None, key=None):
        request = {'Request': 'GetValue', 'Label': self.label}

        if domain:
            request['Domain'] = domain
        if key:
            request['Key'] = key
        self.service.sendPlist(request)
        response = self.service.recvPlist()
        if response:
            r = response.get('Value')
            if hasattr(r, 'data'):
                return r.data
            return r

    def startService(self, name):
        if not self.paired:
            raise NotPairedError

        self.service.sendPlist({
            'Request': 'StartService',
            'Service': name
            })
        StartService = self.service.recvPlist()

        if not StartService:
            return
        if 'Error' in StartService:
            raise StartServiceError(StartService['Error'])
        return PlistService(StartService['Port'])

if __name__ == '__main__':
    l = LockdownClient()
    n = writeHomeFile(HOMEFOLDER, '%s_infos.plist' % l.udid, plistlib.writePlistToString(l.allValues))
    print 'Wrote infos to %s' % n
