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

import sys
import os

try:
    from java.lang import System
except ImportError:
    raise RuntimeError("Only Jython is supported")

# Disable SSL/TLS socket randomization that iOS doesn't like
System.setProperty('jsse.enableCBCProtection', 'false')

# Working directory, a missing variable in Python
# Should work in all cases
wd = os.path.join(os.getcwd(), "tmp", "pymobiledevice")
lib_dir = os.path.join(wd, 'libs')

# Makes importing 3rd party libraries easier
sys.path.append(os.path.join(lib_dir, 'python'))

# Jython doesn't have an OS constant
os_name = System.getProperty('os.name').encode('ascii', 'ignore')

if not os_name.lower().startswith(('windows', 'mac os x', 'linux')):
    raise RuntimeError("Unsupported OS: " + os_name)

# Junixsocket native dependencies
System.setProperty('org.newsclub.net.unix.library.path', os.path.join(lib_dir, 'native'))
jar_dir = os.path.join(lib_dir, 'java')
for jar in os.listdir(jar_dir):
    if not (os._name == 'nt' and jar.startswith('junixsocket')):  # Don't load junixsocket in Windows
        sys.path.append(os.path.join(jar_dir, jar))
