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
from optparse import OptionParser
from afc import AFCClient, AFCShell
from lockdown import LockdownClient


def house_arrest(lockdown, applicationId):
    try:
        mis = lockdown.startService("com.apple.mobile.house_arrest")
    except:
        lockdown = LockdownClient()
        mis = lockdown.startService("com.apple.mobile.house_arrest")

    if not mis:
        return
    mis.sendPlist({"Command": "VendDocuments", "Identifier": applicationId})
    res = mis.recvPlist()
    #pprint(res)
    error = res.get("Error")
    if error:
        print res["Error"]
        return
    return AFCClient(lockdown, service=mis)


def house_arrest_shell(lockdown, applicationId):
    afc = house_arrest(lockdown, applicationId)
    AFCShell(afc=afc).cmdloop()
    #print afc.read_directory("/")


"""
"Install"
"Upgrade"
"Uninstall"
"Lookup"
"Browse"
"Archive"
"Restore"
"RemoveArchive"
"LookupArchives"
"CheckCapabilitiesMatch"

installd
if stat("/var/mobile/tdmtanf") => "TDMTANF Bypass" => SignerIdentity bypass
"""


def mobile_install(lockdown, ipaPath):
    #Start afc service & upload ipa
    afc = AFCClient(lockdown)
    afc.set_file_contents("/" + os.path.basename(ipaPath), open(ipaPath, 'rb').read())
    mci = lockdown.startService("com.apple.mobile.installation_proxy")
    #print mci.sendPlist({"Command":"Archive","ApplicationIdentifier": "com.joystickgenerals.STActionPig"})
    mci.sendPlist({"Command": "Install", "PackagePath": os.path.basename(ipaPath)})
    while True:
        z = mci.recvPlist()
        if not z:
            break
        completion = z.get('PercentComplete')
        if completion:
            print 'Installing, %s: %s %% Complete' % (ipaPath, z['PercentComplete'])
        if z.get('Status') == 'Complete':
            print "Installation %s\n" % z['Status']
            break


def list_apps(lockdown):
    mci = lockdown.startService("com.apple.mobile.installation_proxy")
    #print
    mci.sendPlist({"Command": "Lookup"})
    res = mci.recvPlist()
    for app in res["LookupResult"].values():
        if app.get("ApplicationType") != "System":
            print app["CFBundleIdentifier"], "=>", app.get("Container")
        else:
            print app["CFBundleIdentifier"], "=>", app.get("CFBundleDisplayName")


def get_apps_BundleID(lockdown, appType="User"):
    appList = []
    mci = lockdown.startService("com.apple.mobile.installation_proxy")
    mci.sendPlist({"Command": "Lookup"})
    res = mci.recvPlist()
    for app in res["LookupResult"].values():
        if app.get("ApplicationType") == appType:
            appList.append(app["CFBundleIdentifier"])
        #else: #FIXME
        #    appList.append(app["CFBundleIdentifier"])
    mci.close()
    #pprint(appList)
    return appList


if __name__ == "__main__":
    parser = OptionParser(usage="%prog")
    parser.add_option("-l", "--list", dest="list", action="store_true", default=False,
                      help="List installed applications (non system apps)")
    parser.add_option("-a", "--app", dest="app", action="store", default=None,
                      metavar="FILE", help="Access application files with AFC")
    parser.add_option("-i", "--install", dest="installapp", action="store", default=None,
                      metavar="FILE", help="Install an application package")

    (options, args) = parser.parse_args()
    if options.list:
        lockdown = LockdownClient()
        list_apps(lockdown)
    elif options.app:
        lockdown = LockdownClient()
        house_arrest_shell(lockdown, options.app)
    elif options.installapp:
        lockdown = LockdownClient()
        mobile_install(lockdown, options.installapp)
    else:
        parser.print_help()
