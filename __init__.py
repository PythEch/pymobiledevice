import os
import sys
import site
import inspect

try:
    from java.lang import System
except ImportError:
    raise RuntimeError("Only Jython is supported.")

# Disable SSL/TLS socket randomization that iOS doesn't like
System.setProperty('jsse.enableCBCProtection', 'false')

# Working directory, a missing variable in Python
# Should work in all cases
wd = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
lib_dir = os.path.join(wd, 'libs')

# Makes importing 3rd party libraries easier
site.addsitedir(os.path.join(lib_dir, 'python'))

# Jython doesn't have an OS constant
os_name = System.getProperty('os.name').encode('ascii', 'ignore').lower()

if 'windows' in os_name:
    pass
elif 'os x' in os_name or 'linux' in os_name:
    System.setProperty('org.newsclub.net.unix.library.path', os.path.join(lib_dir, 'native'))
else:
    raise RuntimeError("Unsupported OS: " + os_name)

jar_dir = os.path.join(lib_dir, 'java')
if len([s for s in sys.path if jar_dir in s]) == 0:
    for jar in os.listdir(jar_dir):
        sys.path.append(os.path.join(jar_dir, jar))
#else:
    #Jython is embedded in Java. Let Java take care of the jar dependencies.
