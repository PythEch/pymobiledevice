#
# pymobiledevice - Jython implementation of libimobiledevice
#
# Copyright (C) 2014  Taconut <https://github.com/Triforce1>
# Copyright (C) 2014  PythEch <https://github.com/PythEch>
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

# Special Thanks: https://github.com/mountainstorm

from lockdown import LockdownClient

PORTRAIT = 1
PORTRAIT_UPSIDE_DOWN = 2
LANDSCAPE = 3  # home button to right
LANDSCAPE_HOME_TO_LEFT = 4


class SpringboardClient(object):
    def __init__(self, lockdown=None):
        if lockdown:
            self.lockdown = lockdown
        else:
            self.lockdown = LockdownClient()
        self.service = self.lockdown.startService("com.apple.springboardservices")

    def get_iconstate(self):
        return self.service.sendRequest({
            'command': 'getIconState',
            'formatVersion': '2'
            })[0]

    def set_iconstate(self, state):
        self.service.sendPlist({
            'command': 'setIconState',
            'iconState': state
            })

    def get_iconpngdata(self, bundleid):
        return self.service.sendRequest({
            'command': 'getIconPNGData',
            'bundleId': bundleid
        })['pngData'].data

    def get_interface_orientation(self):
        response = self.service.sendRequest({'command': 'getInterfaceOrientation'})
        if response is None or 'interfaceOrientation' not in response:
            raise RuntimeError('Unable to retrieve interface orientation')
        return response['interfaceOrientation']

    def get_wallpaper_pngdata(self):
        return self.service.sendRequest({'command': 'getHomeScreenWallpaperPNGData'})['pngData'].data
