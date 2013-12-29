#!/usr/bin/env python

from pymobiledevice import apps
from pymobiledevice.afc import AFCClient
from os import makedirs, walk, listdir, sep
from os.path import exists, isdir, abspath, dirname
from posixpath import join
from argparse import ArgumentParser, RawTextHelpFormatter
from shutil import rmtree
import zipfile

class libapp:
    def __init__(self, appid=None):
        """Give 'appid' as a parameter if you want to use house_arrest"""
        # Initiliaze LockdownClient
        try:
            self.lockdown = apps.LockdownClient()
        except Exception as err:
            print "Error: Pairing failed!"
            print err
            return
        # house_arrest
        if appid != None:
            self.appid=appid
            try:
                self.afc = apps.house_arrest(self.lockdown, appid)
            except Exception as err:
                print "Error: Unexpected error with house_arrest!"
                print err
                return
        # afcclient
        else:
            try:
                self.afc = AFCClient(self.lockdown)
            except Exception as err:
                print "Error: Unexpected error with AFCClient!"
                print err
                return

    def verify_path(self, path):
        if not exists(path):
            makedirs(path)
        elif not isdir(path):
            print "Error: %s is not dir..." % path
            return
        
    def backup_app(self, ipaPath, backup_app_data=False):
        path = "tmp/"
        if exists(path):
            rmtree(path)
        self.verify_path(path)
        ipaDir=dirname(ipaPath)
        if ipaDir != "":
            self.verify_path(ipaDir)
        
        try:
            files = self.afc.read_directory('.')[2:]
        except AttributeError:
            print "Error: Unknown identifier '%s'" % self.appid
            return
        app = [x for x in files if x.endswith('.app')]
        if app == []:
            print "Error: Cannot find .app directory!"
            return
        app=app[0]
        self.recursive_save(join(path, 'Payload', app), join('.', app)) #save .app
        
        if not ('iTunesMetadata.plist' in files and 'iTunesArtwork' in files):
            print "Error: iTunesMetadata.plist or iTunesArtwork not found!"
            return
        for i in ('iTunesMetadata.plist', 'iTunesArtwork'):
            self.save_file(i, join(path, i))

        if backup_app_data:
            if 'Library' in files:
                self.recursive_save(join(path, 'Container', 'Library'), join('.', 'Library'))
            if 'Documents' in files:
                self.recursive_save(join(path, 'Container', 'Documents'), join('.', 'Documents'))

        with zipfile.ZipFile(ipaPath, 'w') as zipf:
            for root, dirs, files in walk(path):
                for f in files:
                    src=join(root, f)
                    zipf.write(src, src.replace(path,''))
        rmtree(path)
                    
    def backup_app_data(self, path):
        self.verify_path(path)

        files = self.afc.read_directory('.')[2:]
        if 'Library' in files:
            self.recursive_save(join(path, self.appid, 'Library'), join('.', 'Library'))
        if 'Documents' in files:
            self.recursive_save(join(path, self.appid, 'Documents'), join('.', 'Documents'))

    def save_file(self, afcsrc, target):
        try:
            with open(target, 'wb') as f:
                f.write(self.afc.get_file_contents(afcsrc))
        except Exception as err:
            print "Error: Cannot transfer files iDevice -> PC"
            print err
            return
            
    def upload_file(self, src, afctarget):
        try:
            self.afc.set_file_contents(afctarget, open(src,'rb').read())
            print "Successfully uploaded %s to /var/mobile/Media/%s" % (abspath(src), afctarget)
        except Exception as err:
            print "Error: Cannot transfer files PC -> iDevice"
            print err
            return
            
    def recursive_save(self, path, afcpath='.'):
        dirs=[]
        self.verify_path(path)
        
        for i in self.afc.read_directory(afcpath)[2:]: #list directory (like ls or dir)
            target=join(path,i)
            afcsrc=join(afcpath, i)
            if self.afc.get_file_info(afcsrc)['st_ifmt'] == 'S_IFDIR': #afc_is_dir
                dirs.append(i)
            else:
                self.save_file(afcsrc, target)
        for folder in dirs:
            self.recursive_save(join(path,folder), join(afcpath, folder))

    def install_app(self, ipaPath):
        try:
            apps.mobile_install(self.lockdown, ipaPath)
        except Exception as err:
            print "Error: Unexpected error with mobile installation_proxy!"
            print err
            return
    def list_apps(self):
        try:
            apps.list_apps(self.lockdown)
        except Exception as err:
            print "Error: Unexpected error with mobile installation_proxy!"
            print err
            return


if __name__ == "__main__":
    parser = ArgumentParser(description="a pymobiledevice front-end", formatter_class=RawTextHelpFormatter,
            epilog="""example of use:
%(prog)s -l
%(prog)s -u /home/passwords.zip donotdelete.zip
%(prog)s -s jailbreak.log tmp/jailbreak.log
%(prog)s --install "C:\\Alien Blue.ipa"
%(prog)s -b 0 com.designshed.alienblue "apps/Alien Blue.ipa"
%(prog)s -d com.imangi.templerun2 saves/""")
    parser.add_argument("args", nargs="*")
    parser.add_argument("-l", "--list", action="store_true", help="Lists installed apps\n\n")
    parser.add_argument("-u", "--upload", action="store_true", help="Uploads a file from PC to iDevice.\nArgs: <Source> <Target>\n\n")
    parser.add_argument("-s", "--save", action="store_true", help="Saves a file from iDevice to PC.\nArgs: <Source> <Target>\n\n")
    parser.add_argument("-i", "--install", action="store_true", help="Installs an app from specified source.\nArgs: <IPAPath>\n\n")
    parser.add_argument("-b", "--backup", action="store", metavar="<integer>", type=int, help=
                    "Backups an app as .ipa file with specified Application\nIdentifier.\n\nUse -b 1 option if you want to backup app data as well.\nArgs: <AppID> <IPAPath>\n\n")
    parser.add_argument("-d", "--backupdata", action="store_true", help="Backups an application's data.\nArgs: <AppID> <Directory>")
    
    args = parser.parse_args()
    if args.list:
        libapp().list_apps()
    elif args.upload:
        if len(args.args) == 2:
            libapp().upload_file(args.args[0], args.args[1])
        else:
            parser.print_help()
    elif args.save:
        if len(args.args) == 2:
            libapp().save_file(args.args[0], args.args[1])
        else:
            parser.print_help()
    elif args.install:
        if len(args.args) == 1:
            libapp().install_app(args.args[0])
        else:
            parser.print_help()
    elif args.backup != None:
        if len(args.args) == 2:
            libapp(args.args[0]).backup_app(args.args[1], args.backup)
        else:
            parser.print_help()
    elif args.backupdata:
        if len(args.args) == 2:
            libapp(args.args[0]).backup_app_data(args.args[1])
        else:
            parser.print_help()
    else:
        parser.print_help()
