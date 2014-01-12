import site, os, sys, inspect
site.addsitedir(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))


if 'java' in sys.platform.lower():
    wd = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'netty')
    for jar in os.listdir(wd):
        sys.path.append(os.path.join(wd, jar))
    
