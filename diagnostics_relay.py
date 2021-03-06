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

from pprint import pprint
from lockdown import LockdownClient

MobileGestaltKeys = [
    "DieId", "SerialNumber", "UniqueChipID", "WifiAddress", "CPUArchitecture", "BluetoothAddress",
    "EthernetMacAddress", "FirmwareVersion", "MLBSerialNumber", "ModelNumber", "RegionInfo", "RegionCode",
    "DeviceClass", "ProductType", "DeviceName", "UserAssignedDeviceName", "HWModelStr", "SigningFuse",
    "SoftwareBehavior", "SupportedKeyboards", "BuildVersion", "ProductVersion", "ReleaseType", "InternalBuild",
    "CarrierInstallCapability", "IsUIBuild", "InternationalMobileEquipmentIdentity", "MobileEquipmentIdentifier",
    "DeviceColor", "HasBaseband", "SupportedDeviceFamilies", "SoftwareBundleVersion", "SDIOManufacturerTuple",
    "SDIOProductInfo", "UniqueDeviceID", "InverseDeviceID", "ChipID", "PartitionType", "ProximitySensorCalibration",
    "CompassCalibration", "WirelessBoardSnum", "BasebandBoardSnum", "HardwarePlatform", "RequiredBatteryLevelForSoftwareUpdate",
    "IsThereEnoughBatteryLevelForSoftwareUpdate", "BasebandRegionSKU", "encrypted-data-partition", "SysCfg", "DiagData",
    "SIMTrayStatus", "CarrierBundleInfoArray", "AllDeviceCapabilities", "wi-fi", "SBAllowSensitiveUI", "green-tea",
    "not-green-tea", "AllowYouTube", "AllowYouTubePlugin", "SBCanForceDebuggingInfo", "AppleInternalInstallCapability",
    "HasAllFeaturesCapability", "ScreenDimensions", "IsSimulator", "BasebandSerialNumber", "BasebandChipId", "BasebandCertId",
    "BasebandSkeyId", "BasebandFirmwareVersion", "cellular-data", "contains-cellular-radio", "RegionalBehaviorGoogleMail",
    "RegionalBehaviorVolumeLimit", "RegionalBehaviorShutterClick", "RegionalBehaviorNTSC", "RegionalBehaviorNoWiFi",
    "RegionalBehaviorChinaBrick", "RegionalBehaviorNoVOIP", "RegionalBehaviorAll", "ApNonce"
]


class DIAGClient(object):
    def __init__(self, lockdown=None, serviceName="com.apple.mobile.diagnostics_relay"):
        if lockdown:
            self.lockdown = lockdown
        else:
            self.lockdown = LockdownClient()

        self.service = self.lockdown.startService(serviceName)
        self.packet_num = 0

    def stop_session(self):
        print "Disconecting..."
        self.service.close()

    def query_mobilegestalt(self, MobileGestalt=MobileGestaltKeys):
        self.service.sendPlist({"Request": "MobileGestalt", "MobileGestaltKeys": MobileGestalt})
        res = self.service.recvPlist()
        #pprint(res)
        if "Diagnostics" in res:
            return res

    def action(self, action="Shutdown", flags=None):
        self.service.sendPlist({"Request": action})
        res = self.service.recvPlist()
        #pprint(res)
        return res

    def restart(self):
        return self.action("Restart")

    def shutdown(self):
        return self.action("Shutdown")

    def diagnostics(self, diagType="All"):
        self.service.sendPlist({"Request": diagType})
        res = self.service.recvPlist()
        pprint(res)
        if "Diagnostics" in res:
            return res

    def ioregistry_entry(self, name=None, ioclass=None):
        req = {"Request": "IORegistry"}
        if name:
            req["EntryName"] = name

        if ioclass:
            req["EntryClass"] = ioclass

        self.service.sendPlist(req)
        res = self.service.recvPlist()
        pprint(res)
        if "Diagnostics" in res:
            return res

    def ioregistry_plane(self, plane, ioclass):
        req = {"Request": "IORegistry", "CurrentPlane": ioclass}
        self.service.sendPlist(req)
        res = self.service.recvPlist()
        pprint(res)
        if "Diagnostics" in res:
            return res


if __name__ == "__main__":
    lockdown = LockdownClient()
    ProductVersion = lockdown.getValue("", "ProductVersion")
    assert ProductVersion[0] >= "4"

    diag = DIAGClient()
    diag.diagnostics()
    diag.query_mobilegestalt()
    diag.restart()
