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

from afc import AFCClient, AFCShell, AFCFile
from lockdown import LockdownClient


class InstallationProxy(object):
    def __init__(self, lockdown=None):
        if lockdown:
            self.lockdown = lockdown
        else:
            self.lockdown = LockdownClient()

        self.service = self.lockdown.startService('com.apple.mobile.installation_proxy')

    def install_ipa(self, ipaPath):
        #Start afc service & upload ipa
        filename = os.path.basename(ipaPath)
        with AFCFile(name='/'+filename, mode='wb', afc=AFCClient(self.lockdown)) as f:
            f.write(open(ipaPath, 'rb').read())

        self.service.sendPlist({
            'Command': 'Install',
            'PackagePath': filename
            })

        while True:
            response = self.service.recvPlist()
            if not response:
                break

            completion = response.get('PercentComplete')
            if completion:
                print 'Installing, %s: %s %% Complete' % (ipaPath, completion)
            status = response.get('Status')
            if status == 'Complete':
                print 'Installation %s' % status
                break

    def app_info(self):
        return self.service.sendRequest({'Command': 'Lookup'})['LookupResult']

    def list_user_apps(self):
        return [[app['CFBundleIdentifier'], app.get('CFBundleDisplayName'), app.get('Container')]
                for app in self.app_info().values()
                if app.get('ApplicationType') == 'User']

    def list_system_apps(self):
        return [[app['CFBundleIdentifier'], app.get('CFBundleDisplayName')]
                for app in self.app_info().values()
                if app.get('ApplicationType') == 'System']

    def list_user_apps_BundleID(self):
        return [app['CFBundleIdentifier']
                for app in self.app_info().values()
                if app.get('ApplicationType') == 'User']

    def list_system_apps_BundleID(self):
        return [app['CFBundleIdentifier']
                for app in self.app_info().values()
                if app.get('ApplicationType') == 'System']

    def list_all_apps_BundleID(self):
        return self.app_info().keys()

    def close(self):
        self.service.close()

    def __del__(self):
        self.close()


class AFCApplication(AFCClient):
    def __init__(self, lockdown, applicationBundleID):
        super(AFCApplication, self).__init__(lockdown, 'com.apple.mobile.house_arrest')

        response = self.service.sendRequest({
            'Command': 'VendDocuments',
            'Identifier': applicationBundleID
            })

        error = response.get('Error')
        if error:
            print error  # FIXME

    @classmethod
    def as_shell(cls, lockdown, applicationBundleID):
        _afc = cls(lockdown, applicationBundleID)
        AFCShell(afc=_afc).cmdloop()
