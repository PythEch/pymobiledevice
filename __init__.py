import site, os, sys, inspect
site.addsitedir(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))
