import site, os, sys, inspect, java

if not 'java' in sys.platform.lower():
    raise RuntimeError("Unsupported platform: " + sys.platform)

platform = java.lang.System.getProperty('os.name').encode('ascii', 'ignore').lower()
if 'windows' in platform:
    iswindows = True
elif 'os x' in platform:
    raise NotImplementedError("Your OS is not supported yet: " + platform)
elif 'linux' in platform:
    raise NotImplementedError("Your OS is not supported yet: " + platform)
else:
    raise RuntimeError("Unsupported OS: " + platform)

java.lang.System.setProperty("jsse.enableCBCProtection", "false")

#working directory
wd = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

site.addsitedir(wd)

jar_dir = os.path.join(wd, 'jar')
for jar in os.listdir(jar_dir):
    sys.path.append(os.path.join(jar_dir, jar))
    
