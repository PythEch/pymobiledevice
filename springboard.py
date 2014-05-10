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


class Springboard(object):
    PORTRAIT = 1
    PORTRAIT_UPSIDE_DOWN = 2
    LANDSCAPE = 3  # home button to right
    LANDSCAPE_HOME_TO_LEFT = 4

    def __init__(self, lockdown):
        self.lockdown = lockdown
        self.service = self.lockdown.startService("com.apple.springboardservices")

    def get_iconstate(self):
        self.service.sendPlist({
            'command': 'getIconState',
            'formatVersion': '2'
            })
        return self.service.recvPlist()

    def set_iconstate(self, state):
        self.service.sendPlist({
            'command': 'setIconState',
            'iconState': state
            })

    def get_iconpngdata(self, bundleid):
        self.service.sendPlist({
            'command': 'getIconPNGData',
            'bundleId': bundleid
        })
        return self.service.recvPlist()['pngData']

    def get_interface_orientation(self):
        self.service.sendPlist({
            'command': 'getInterfaceOrientation'
            })
        reply = self.service.recvPlist()
        if reply is None or 'interfaceOrientation' not in reply:
            raise RuntimeError('Unable to retrieve interface orientation')
        return reply['interfaceOrientation']

    def get_wallpaper_pngdata(self):
        self.service.sendPlist({
            'command': 'getHomeScreenWallpaperPNGData'
            })
        return self.service.recvPlist()['pngData']
