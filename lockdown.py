from plist_service import PlistService
from pprint import pprint
import os
import plistlib
import uuid
import platform
import java

if "Windows" in java.lang.System.getProperty('os.name').encode('ascii','ignore'):
    HOMEFOLDER = os.path.join(os.environ["ALLUSERSPROFILE"], "Apple", "Lockdown")
else: #Linux won't work?
    HOMEFOLDER = "/var/db/lockdown/"

class LockdownClient(object):
    def __init__(self,udid=None):
        self.SessionID = None
        self.c = None
        self.c = PlistService(62078,udid)
        self.hostID = self.generate_hostID()
        #print "HostID : ", self.hostID
        self.paired = False
        self.label = "pyMobileDevice"
        self.c.sendPlist({"Request":"QueryType"})
        res = self.c.recvPlist()
        assert res["Type"] == "com.apple.mobile.lockdown"
        self.udid = self.getValue("", "UniqueDeviceID")
        #print "Device Name : ", self.getValue("", "DeviceName")
        self.allValues = self.getValue("", "")
        self.UniqueChipID = self.allValues.get("UniqueChipID")
        #self.DevicePublicKey = ""
        self.DevicePublicKey =  self.getValue("", "DevicePublicKey")

        #pprint(self.allValues)
        #self.udid  = self.c.udid
        self.identifier = self.udid
        #if not self.identifier:
        #    if self.UniqueChipID:
        #        self.identifier = "%x" % self.UniqueChipID
        #    else:
        #        print "Could not get UDID or ECID, failing"
        #        raise
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
        pair_record = None
        certPem = None
        privateKeyPem = None
        pair_record = plistlib.readPlist(os.path.join(HOMEFOLDER, "%s.plist" % self.identifier))
        ValidatePair = {"Request": "ValidatePair", "PairRecord": pair_record}
        self.c.sendPlist(ValidatePair)
        ValidatePair = self.c.recvPlist()
        if not ValidatePair or ValidatePair.has_key("Error"):
            pair_record = None
            print "ValidatePair fail", ValidatePair
            return False
        self.paired = True
        #print "Validate Pairing OK", ValidatePair
        d = {"Request": "StartSession", "HostID": pair_record.get("HostID", self.hostID)}
        self.c.sendPlist(d)
        startsession = self.c.recvPlist() 
        #print "Starting session",startsession
        self.SessionID = startsession.get("SessionID")
        return True
    
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
