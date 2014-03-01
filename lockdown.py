from plist_service import PlistService
from pprint import pprint
from certificate import ca_do_everything
from util import write_file, readHomeFile, writeHomeFile
import os
import plistlib
import uuid
#import socket
import platform
import time

#we store pairing records and ssl keys in ~/.pymobiledevice
HOMEFOLDER = os.path.join(os.environ["HOMEPATH"], ".pymobiledevice")

class LockdownClient(object):
    def __init__(self,udid=None):
        self.c = PlistService(62078,udid)
        self.hostID = self.generate_hostID()
        self.paired = False
        self.label = "pyMobileDevice"
        self.c.sendPlist({"Request":"QueryType"})
        res = self.c.recvPlist()
        assert res["Type"] == "com.apple.mobile.lockdown"
        self.allValues = self.getValue("", "")
        self.udid = self.allValues.get("UniqueDeviceID")
        self.osVersion = self.allValues.get("ProductVersion")
        self.is_iOS7 = (self.osVersion[0] == "7")
        self.DevicePublicKey = self.allValues.get("DevicePublicKey").data
        
        if not self.validate_pairing():
            if not self.pair():
                return
            if self.is_iOS7: #usbmux is resetted
                time.sleep(5) #FIXME: What happens if this takes more than 5 seconds?
                self.__init__(self.udid)
                return
            self.validate_pairing()

    def generate_hostID(self):
        #hostname = socket.gethostname()
        hostname = platform.node()
        hostid = uuid.uuid3(uuid.NAMESPACE_DNS, hostname)
        return str(hostid).upper()

        
    #def __del__(self):
    #    self.stop_session()
    #    if self.c :
    #        self.c.sendPlist({"Request": "Goodbye"})
    #        res = self.c.recvPlist()
    #        return res
    #    #if not res or res.get("Result") != "Success":
    #    #    print "Goodbye fail :", res
       
    def enter_recovery(self):
        self.c.sendPlist({"Request": "EnterRecovery"})
        print self.c.recvPlist()
    
    def stop_session(self):
        if self.SessionID and self.c:
            self.c.sendPlist({"Request": "StopSession", "SessionID": self.SessionID})
            self.SessionID = None
            res = self.c.recvPlist()
            return res
            #pprint(res)
            #if not res or res.get("Result") != "Success":
            #    print "StopSession fail :", res
                    
    def validate_pairing(self):
        record = readHomeFile(HOMEFOLDER, "%s.plist" % self.udid)
        if record:
            pair_record = plistlib.readPlistFromString(record)
            certPem = pair_record["HostCertificate"].data
            privateKeyPem = pair_record["HostPrivateKey"].data
            print "Found pairing record for device %s" % self.udid
        else:
            print "No pairing record found for device %s" % self.udid
            return False
        if False:
            if sys.platform == "win32":
                folder = os.environ["ALLUSERSPROFILE"] + "/Apple/Lockdown/"
            elif sys.platform == "darwin":
                folder = "/var/db/lockdown/"
            pair_record = plistlib.readPlist(folder + "%s.plist" % self.udid)
            print "Using iTunes pair record"
            
        ValidatePair = {"Request": "ValidatePair", "PairRecord": pair_record}
        self.c.sendPlist(ValidatePair)
        ValidatePair = self.c.recvPlist()
        if not ValidatePair or "Error" in ValidatePair:
            pair_record =None
            print "ValidatePair fail", ValidatePair
            return False
        self.paired = True
        #print "Validate Pairing OK", ValidatePair
        d = {"Request": "StartSession", "HostID": pair_record.get("HostID", self.hostID)}
        self.c.sendPlist(d)
        startsession = self.c.recvPlist() 
        #print "Starting session",startsession
        self.SessionID = startsession.get("SessionID")
        if startsession.get("EnableSessionSSL"):
            sslfile = self.udid + "_ssl.txt"
            sslfile = writeHomeFile(HOMEFOLDER, sslfile, certPem + "\n" + privateKeyPem)
            self.c.ssl_start(sslfile, sslfile)
            #print "SSL started"
            self.udid = self.getValue("", "UniqueDeviceID")
            self.allValues = self.getValue("", "")
            #print "UDID", self.udid
        return True

    def pair(self, pair_record=None):
        if not pair_record:
            print "Got device public key"
            print "Creating host key & certificate"
            certPem, privateKeyPem, DeviceCertificate = ca_do_everything(self.DevicePublicKey)

            pair_record = {"DevicePublicKey": plistlib.Data(self.DevicePublicKey),
                           "DeviceCertificate": plistlib.Data(DeviceCertificate),
                           "HostCertificate": plistlib.Data(certPem),
                           "HostPrivateKey": plistlib.Data(privateKeyPem),
                           "HostID": self.hostID,
                           "RootCertificate": plistlib.Data(certPem),
                           "SystemBUID": "30142955-444094379208051516"
            }
            
        Pair = {"Request": "Pair", "PairRecord": pair_record}
        self.c.sendPlist(Pair)
        Pair = self.c.recvPlist()
        if "Error" in Pair and self.is_iOS7 and Pair["Error"] == "PasswordProtected":
            print "\n\nPlease tap 'Trust This Computer' on your iDevice...\n"
            time.sleep(5)
            return self.pair(pair_record)
        if Pair and Pair.get("Result") == "Success" or Pair.has_key("EscrowBag"):
            if Pair.has_key("EscrowBag"):
                pair_record["EscrowBag"] = Pair["EscrowBag"]
            writeHomeFile(HOMEFOLDER, "%s.plist" % self.udid, plistlib.writePlistToString(pair_record))
            return True
        print "Pairing error", Pair
        return False
    
    def getValue(self, domain=None, key=None):
        req = {"Request":"GetValue", "Label": self.label}
        
        if domain:
            req["Domain"] = domain
        if key:
            req["Key"] = key
        self.c.sendPlist(req)
        res = self.c.recvPlist()
        if res:
            r = res.get("Value")
            if hasattr(r, "data"):
                return r.data
            return r
        
    def startService(self, name):
        if not self.paired:
            print "Cannot startService %s, not paired" % name
            return
        self.c.sendPlist({"Request": "StartService", "Service": name})
        StartService = self.c.recvPlist()
        if not StartService:
            return
        if StartService.has_key("Error"):
            print StartService["Error"], name
            return
        #print StartService
        zz = PlistService(StartService["Port"])
        return zz

if __name__ == "__main__":
    l = LockdownClient()
    n = writeHomeFile(HOMEFOLDER, "%s_infos.plist" % l.udid, plistlib.writePlistToString(l.allValues))
    print "Wrote infos to %s" % n
