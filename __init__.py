import os
import sys
import platform
import site
import inspect

try:
    from java.lang import System
except ImportError:
    if hasattr(platform, 'python_implementation'): # Added in Python 2.6
        raise RuntimeError("Unsupported implementation: " + platform.python_implementation())
    else:
        raise RuntimeError("Only Jython is supported")

# Jython doesn't have an OS constant
os_name = System.getProperty('os.name').encode('ascii', 'ignore').lower()

if 'os x' in os_name or 'linux' in os_name:
    raise NotImplementedError("Your OS is not supported yet: " + os_name)
elif 'windows' not in os_name:
    raise RuntimeError("Unsupported OS: " + os_name)

# Disable SSL/TLS socket randomization that iOS doesn't like
System.setProperty('jsse.enableCBCProtection', 'false')

# Working directory, a missing variable in Python
# Should work in all cases
wd = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

# Makes importing 3rd party libraries easier
site.addsitedir(wd)

if len([s for s in sys.path if 'pymobiledevice\\jar\\' in s]) == 0:
    jar_dir = os.path.join(wd, 'jar')
    for jar in os.listdir(jar_dir):
        sys.path.append(os.path.join(jar_dir, jar))
#else:
    #Jython is embedded in Java. Let Java take care of the jar dependencies.
