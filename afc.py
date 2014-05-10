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
import plistlib
import struct
import posixpath
from cmd import Cmd
from construct.core import Struct
from construct.lib.container import Container
from construct.macros import String, ULInt64
from util import hexdump, parsePlist
from lockdown import LockdownClient

AFC_OP_STATUS          = 0x00000001
AFC_OP_DATA            = 0x00000002  # Data
AFC_OP_READ_DIR        = 0x00000003  # ReadDir
AFC_OP_READ_FILE       = 0x00000004  # ReadFile
AFC_OP_WRITE_FILE      = 0x00000005  # WriteFile
AFC_OP_WRITE_PART      = 0x00000006  # WritePart
AFC_OP_TRUNCATE        = 0x00000007  # TruncateFile
AFC_OP_REMOVE_PATH     = 0x00000008  # RemovePath
AFC_OP_MAKE_DIR        = 0x00000009  # MakeDir
AFC_OP_GET_FILE_INFO   = 0x0000000a  # GetFileInfo
AFC_OP_GET_DEVINFO     = 0x0000000b  # GetDeviceInfo
AFC_OP_WRITE_FILE_ATOM = 0x0000000c  # WriteFileAtomic (tmp file+rename)
AFC_OP_FILE_OPEN       = 0x0000000d  # FileRefOpen
AFC_OP_FILE_OPEN_RES   = 0x0000000e  # FileRefOpenResult
AFC_OP_READ            = 0x0000000f  # FileRefRead
AFC_OP_WRITE           = 0x00000010  # FileRefWrite
AFC_OP_FILE_SEEK       = 0x00000011  # FileRefSeek
AFC_OP_FILE_TELL       = 0x00000012  # FileRefTell
AFC_OP_FILE_TELL_RES   = 0x00000013  # FileRefTellResult
AFC_OP_FILE_CLOSE      = 0x00000014  # FileRefClose
AFC_OP_FILE_SET_SIZE   = 0x00000015  # FileRefSetFileSize (ftruncate)
AFC_OP_GET_CON_INFO    = 0x00000016  # GetConnectionInfo
AFC_OP_SET_CON_OPTIONS = 0x00000017  # SetConnectionOptions
AFC_OP_RENAME_PATH     = 0x00000018  # RenamePath
AFC_OP_SET_FS_BS       = 0x00000019  # SetFSBlockSize (0x800000)
AFC_OP_SET_SOCKET_BS   = 0x0000001A  # SetSocketBlockSize (0x800000)
AFC_OP_FILE_LOCK       = 0x0000001B  # FileRefLock
AFC_OP_MAKE_LINK       = 0x0000001C  # MakeLink
AFC_OP_SET_FILE_TIME   = 0x0000001E  # set st_mtime

AFC_E_SUCCESS               = 0
AFC_E_UNKNOWN_ERROR         = 1
AFC_E_OP_HEADER_INVALID     = 2
AFC_E_NO_RESOURCES          = 3
AFC_E_READ_ERROR            = 4
AFC_E_WRITE_ERROR           = 5
AFC_E_UNKNOWN_PACKET_TYPE   = 6
AFC_E_INVALID_ARG           = 7
AFC_E_OBJECT_NOT_FOUND      = 8
AFC_E_OBJECT_IS_DIR         = 9
AFC_E_PERM_DENIED           = 10
AFC_E_SERVICE_NOT_CONNECTED = 11
AFC_E_OP_TIMEOUT            = 12
AFC_E_TOO_MUCH_DATA         = 13
AFC_E_END_OF_DATA           = 14
AFC_E_OP_NOT_SUPPORTED      = 15
AFC_E_OBJECT_EXISTS         = 16
AFC_E_OBJECT_BUSY           = 17
AFC_E_NO_SPACE_LEFT         = 18
AFC_E_OP_WOULD_BLOCK        = 19
AFC_E_IO_ERROR              = 20
AFC_E_OP_INTERRUPTED        = 21
AFC_E_OP_IN_PROGRESS        = 22
AFC_E_INTERNAL_ERROR        = 23
AFC_E_MUX_ERROR             = 30
AFC_E_NO_MEM                = 31
AFC_E_NOT_ENOUGH_DATA       = 32
AFC_E_DIR_NOT_EMPTY         = 33

AFC_E_MUX_ERROR             = 30
AFC_E_NO_MEM                = 31
AFC_E_NOT_ENOUGH_DATA       = 32
AFC_E_DIR_NOT_EMPTY         = 33

AFC_FOPEN_RDONLY   = 0x00000001  # r   O_RDONLY
AFC_FOPEN_RW       = 0x00000002  # r+  O_RDWR   | O_CREAT
AFC_FOPEN_WRONLY   = 0x00000003  # w   O_WRONLY | O_CREAT  | O_TRUNC
AFC_FOPEN_WR       = 0x00000004  # w+  O_RDWR   | O_CREAT  | O_TRUNC
AFC_FOPEN_APPEND   = 0x00000005  # a   O_WRONLY | O_APPEND | O_CREAT
AFC_FOPEN_RDAPPEND = 0x00000006  # a+  O_RDWR   | O_APPEND | O_CREAT

AFC_HARDLINK = 1
AFC_SYMLINK  = 2

AFC_LOCK_SH = 1 | 4  # shared lock
AFC_LOCK_EX = 2 | 4  # exclusive lock
AFC_LOCK_UN = 8 | 4  # unlock


AFCMAGIC = "CFA6LPAA"
AFCPacket = Struct("AFCPacket",
                   String("magic", 8,),
                   ULInt64("entire_length"),
                   ULInt64("this_length"),
                   ULInt64("packet_num"),
                   ULInt64("operation")
                   )
#typedef struct {
#    uint64_t filehandle, size;
#} AFCFilePacket;


class AFCError(IOError):
    lookup_table = {
        AFC_E_SUCCESS: "Success",
        AFC_E_UNKNOWN_ERROR: "Unknown error",
        AFC_E_OP_HEADER_INVALID: "OP header invalid",
        AFC_E_NO_RESOURCES: "No resources",
        AFC_E_READ_ERROR: "Read error",
        AFC_E_WRITE_ERROR: "Write error",
        AFC_E_UNKNOWN_PACKET_TYPE: "Unknown packet type",
        AFC_E_INVALID_ARG: "Invalid argument",
        AFC_E_OBJECT_NOT_FOUND: "Object not found",
        AFC_E_OBJECT_IS_DIR: "Object is directory",
        AFC_E_PERM_DENIED: "Permission denied",
        AFC_E_SERVICE_NOT_CONNECTED: "Service not connected",
        AFC_E_OP_TIMEOUT: "OP timeout",
        AFC_E_TOO_MUCH_DATA: "Too much data",
        AFC_E_END_OF_DATA: "End of data",
        AFC_E_OP_NOT_SUPPORTED: "OP not supported",
        AFC_E_OBJECT_EXISTS: "Object exists",
        AFC_E_OBJECT_BUSY: "Object busy",
        AFC_E_NO_SPACE_LEFT: "No space left",
        AFC_E_OP_WOULD_BLOCK: "OP would block",
        AFC_E_IO_ERROR: "IO error",
        AFC_E_OP_INTERRUPTED: "OP interrupted",
        AFC_E_OP_IN_PROGRESS: "OP in progress",
        AFC_E_INTERNAL_ERROR: "Internal error",
        AFC_E_MUX_ERROR: "MUX error",
        AFC_E_NO_MEM: "No memory",
        AFC_E_NOT_ENOUGH_DATA: "Not enough data",
        AFC_E_DIR_NOT_EMPTY: "Directory not empty"
    }

    def __init__(self, status):
        super(AFCError, self).__init__(status, self.lookup_table.get(status, "Unknown error"))


class AFCClient(object):
    """
    Creates a connection to the iDevice using AFC protocol.

    Attributes:
        `lockdown`: The `LockdownClient` class that should be used for almost everything.
        `serviceName`: The service ID of the protocol.
        `service`: The plist service which is running in the background.
        `packet_num`: Used to track number of packets sent during lifetime of the client.
    """

    def __init__(self, lockdown=None, serviceName='com.apple.afc', service=None):
        """
        Constructor method of `AFCClient`.

        Note:
            `serviceName` is obsolete when `service` parameter is used.
            Although it will be saved as attribute.

        Args:
            `lockdown` (optional): The `LockdownClient` class that should be used for almost everything.
            `serviceName` (optional): Service ID of the protocol, defaults to 'com.apple.afc'.
                Used for abstract class purposes although you can modify if you have good reasons.
            `service` (optional): Useful when you already have a service running.
        """
        if lockdown:
            self.lockdown = lockdown
        else:
            self.lockdown = LockdownClient()

        if service:
            self.service = service
        else:
            self.service = self.lockdown.startService(serviceName)
        self.serviceName = serviceName
        self.packet_num = 0

    def stop_session(self):
        """Disconnects from iDevice."""
        print "Disconecting..."
        self.service.close()

    def __del__(self):
        self.stop_session()

    def dispatch_packet(self, operation, data, this_length=0):
        """
        Dispatches an AFC packet over a client.

        Args:
            `operation`: The operation to do. See the source code for the list of constants.
            `data`: The data to send with header.
            `this_length` (optional): Not sure but, according to C libimobiledevice, it looks
                like size of packet + data length.
        """
        afcpack = Container(magic=AFCMAGIC,
                            entire_length=40 + len(data),
                            this_length=40 + len(data),
                            packet_num=self.packet_num,
                            operation=operation)
        if this_length:
            afcpack.this_length = this_length
        header = AFCPacket.build(afcpack)
        self.packet_num += 1
        self.service.send(header + data)

    def receive_data(self):
        """
        Receives data through an AFC client.

        Returns:
            The response of the iDevice.

        Raises:
            `AFCError` if the operation was not successful.
        """
        res = self.service.recv(40)
        status = AFC_E_SUCCESS
        data = ""
        if res:
            res = AFCPacket.parse(res)
            assert res["entire_length"] >= 40
            length = res["entire_length"] - 40
            data = self.service.recv_exact(length)
            if res.operation == AFC_OP_STATUS:
                assert length == 8
                status = int(struct.unpack("<Q", data[:8])[0])

                if status != AFC_E_SUCCESS:
                    raise AFCError(status)

            elif res.operation != AFC_OP_DATA:
                pass  # print "error ?", res
        return data

    def do_operation(self, operation, data="", this_length=0):
        """
        Dispatches a packet and returns the response.

        Args:
            `operation`: The operation to perform.
            `data` (optional): The data to send.
            `this_length` (optional): Not sure but, according to C libimobiledevice, it looks
                like size of packet + data length.

        Returns:
            The data that is recieved after the operation is done.
        """
        self.dispatch_packet(operation, data, this_length)
        return self.receive_data()

    def list_to_dict(self, d):
        """Converts a primitive key, value array to Python compatible dictionary."""
        it = iter(d.rstrip("\x00").split("\x00"))
        return dict(zip(it, it))

    def get_device_infos(self):
        infos = self.do_operation(AFC_OP_GET_DEVINFO)
        return self.list_to_dict(infos)

    def get_file_info(self, filename):
        data = self.do_operation(AFC_OP_GET_FILE_INFO, filename)
        return self.list_to_dict(data)

    def file_open(self, filename, mode=AFC_FOPEN_RDONLY):
        #if filename.startswith('/var/Mobile/Media') and self.serviceName == 'com.apple.afc':
        #    filename = filename.replace('/var/Mobile/Media', '')

        data = self.do_operation(AFC_OP_FILE_OPEN, struct.pack("<Q", mode) + filename + "\x00")
        return struct.unpack("<Q", data)[0]

    def file_close(self, handle):
        self.do_operation(AFC_OP_FILE_CLOSE, struct.pack("<Q", handle))

    def file_seek(self, handle, offset, whence=os.SEEK_SET):
        self.do_operation(AFC_OP_FILE_SEEK, struct.pack("<QQq", handle, whence, offset))

    def file_tell(self, handle):
        data = self.do_operation(AFC_OP_FILE_TELL, struct.pack("<Q", handle))
        return struct.unpack("<Q", data)[0]

    def file_truncate(self, handle, size=None):
        if size is None:
            size = self.file_tell(handle)

        self.do_operation(AFC_OP_FILE_SET_SIZE, struct.pack("<QQ", handle, size))

    def file_read(self, handle, sz):
        MAXIMUM_READ_SIZE = 1 << 16
        data = ""
        while sz > 0:
            if sz > MAXIMUM_READ_SIZE:
                toRead = MAXIMUM_READ_SIZE
            else:
                toRead = sz

            d = self.do_operation(AFC_OP_READ, struct.pack("<QQ", handle, toRead))

            sz -= toRead
            data += d
        return data

    def file_write(self, handle, data):
        MAXIMUM_WRITE_SIZE = 1 << 15
        hh = struct.pack("<Q", handle)
        segments = len(data) / MAXIMUM_WRITE_SIZE
        for i in xrange(segments):
            self.do_operation(AFC_OP_WRITE,
                              hh + data[i*MAXIMUM_WRITE_SIZE:(i+1)*MAXIMUM_WRITE_SIZE],
                              this_length=48)
        if len(data) % MAXIMUM_WRITE_SIZE:
            self.do_operation(AFC_OP_WRITE,
                              hh + data[segments*MAXIMUM_WRITE_SIZE:],
                              this_length=48)

    def make_link(self, target, linkname, link_type=AFC_SYMLINK):
        self.do_operation(AFC_OP_MAKE_LINK, struct.pack("<Q", link_type) + target + "\x00" + linkname + "\x00")

    def remove_path(self, path):
        self.do_operation(AFC_OP_REMOVE_PATH, path + "\x00")

    def rename_path(self, old, new):
        self.do_operation(AFC_OP_RENAME_PATH, old + "\x00" + new + "\x00")

    def read_directory(self, dirname):
        data = self.do_operation(AFC_OP_READ_DIR, dirname)
        return data.rstrip("\x00").split("\x00")

    def make_directory(self, dirname):
        self.do_operation(AFC_OP_MAKE_DIR, dirname)

    def dir_walk(self, dirname):
        # root = dirname
        dirs = []
        files = []
        for fd in self.read_directory(dirname):
            if fd in ('.', '..', ''):  # is it ever be '' ?
                continue
            if self.get_file_info(posixpath.join(dirname, fd)).get('st_ifmt') == 'S_IFDIR':
                dirs.append(fd)
            else:
                files.append(fd)

        yield dirname, dirs, files

        # if dirs != [], continue iterating using recursion
        if dirs:
            for d in dirs:
                for walk_result in self.dir_walk(posixpath.join(dirname, d)):
                    yield walk_result

    def remove_directory(self, dirname):
        for d in self.read_directory(dirname):
            if d in ('.', '..', ''):
                continue
            path = posixpath.join(dirname, d)
            if self.get_file_info(path).get("st_ifmt") == "S_IFDIR":
                self.remove_directory(path)
            else:
                self.remove_path(path)
        assert len(self.read_directory(dirname)) == 2  # "." and ".."
        self.remove_path(dirname)


class AFC2Client(AFCClient):  # Is this really useful?
    def __init__(self, lockdown=None):
        super(AFC2Client, self).__init__(lockdown, 'com.apple.afc2')


class AFCCrashLog(AFCClient):
    """Provides access to the /var/mobile/Library/Logs/CrashReporter directory"""

    def __init__(self, lockdown=None):
        super(AFCCrashLog, self).__init__(lockdown, 'com.apple.crashreportcopymobile')


class AFCFile(object):
    def __init__(self, name, mode='r+', afc=None):
        flags = {'r': AFC_FOPEN_RDONLY,
                 'r+': AFC_FOPEN_RW,
                 'w': AFC_FOPEN_WRONLY,
                 'w+': AFC_FOPEN_WR,
                 'a': AFC_FOPEN_APPEND,
                 'a+': AFC_FOPEN_RDAPPEND}

        if 'b' in mode or os._name != 'nt':
            self._binary = True
        else:
            self._binary = False

        if afc:
            self._afc = afc
        else:
            self._afc = AFCClient()

        try:
            self._handle = self._afc.file_open(name, flags[mode.replace('b', '', 1)])
        except KeyError:
            raise ValueError("Invalid mode ('%s')" % mode)

        self._info = self._afc.get_file_info(name)

        if self._info['st_ifmt'] == 'S_IFLNK':
            name = self._info['LinkTarget']

        self.name = name
        self.mode = mode
        self.closed = False

    def read(self, size=None):
        try:
            if self.mode in ('w', 'a'):
                raise IOError("File not open for reading")

            if size is None:
                size = int(self._info['st_size'])

            r = self._afc.file_read(self._handle, size)
            if self._binary:
                return r
            return r.replace('\r', '\n').replace('\n', '\r\n')
        except TypeError:
            raise TypeError("an integer is required")
        except AFCError:
            if self.closed:
                raise IOError("I/O operation on closed file")
            raise

    def write(self, string):
        try:
            if self.mode == 'r':
                raise IOError("File not open for writing")

            if not self._binary:
                string = string.replace('\r\n', '\n').replace('\r', '\n')
            self._afc.file_write(self._handle, string)
        except TypeError:
            raise TypeError("expected a character buffer object")
        except AFCError:
            if self.closed:
                raise IOError("I/O operation on closed file")
            raise

    def readlines(self, size=None):
        return self.read(size).splitlines(True)

    def writelines(self, sequence_of_strings):
        try:
            for string in sequence_of_strings:
                self.write(string + "\n")
        except TypeError:
            raise TypeError("writelines() requires an iterable argument")

    def close(self):
        self._afc.file_close(self._handle)
        self.closed = True

    def seek(self, offset, whence=os.SEEK_SET):
        try:
            self._afc.file_seek(self._handle, offset, whence)
        except AFCError:
            if self.closed:
                raise IOError("I/O operation on closed file")
            raise

    def tell(self):
        try:
            return self._afc.file_tell(self._handle)
        except AFCError:
            if self.closed:
                raise IOError("I/O operation on closed file")
            raise

    def truncate(self, size=None):
        try:
            self._afc.file_truncate(self._handle, size)
        except AFCError:
            if self.closed:
                raise IOError("I/O operation on closed file")
            raise

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        #if exception_type:
        #    return  # FIXME: do something
        self.close()

    def __del__(self):
        self.close()

    # Not sure if this is the most elegant solution
    # Tested and working though
    def __iter__(self):
        r = ""
        buffer_size = 4096  # What's optimal for this?
        while True:
            buff = self.read(buffer_size)
            if buff:
                r += buff
            else:
                # Reached EOF
                if r:  # yield the last line if it wasn't already
                    yield r
                break

            lines = r.splitlines(True)
            r = ""
            for line in lines:
                if line[-1] == '\n':
                    yield line
                else:
                    r = line  # Continue reading

    xreadlines = __iter__

# AFCShell is doomed because of try-catch approach
# This makes coding AFCClient easier and AFCShell harder.
# I'm thinking about a solution

class AFCShell(Cmd):
    def __init__(self, completekey='tab', stdin=None, stdout=None, afc=None):
        super(AFCShell, self).__init__(self, completekey=completekey, stdin=stdin, stdout=stdout)
        if afc:
            self.afc = afc
        else:
            self.lockdown = LockdownClient()
            self.afc = AFCClient(self.lockdown)

        self.prompt = "(AFC) / "
        self.curdir = "/"
        self.complete_cat = self._complete
        self.complete_ls = self._complete

    def do_exit(self, p):
        return True  # ???

    def do_quit(self, p):
        return True  # ???

    def do_pwd(self, p):
        return self.curdir

    def do_link(self, p):
        z = p.split()
        self.afc.make_link(AFC_SYMLINK, z[0], z[1])

    def do_cd(self, p):
        if not p.startswith("/"):
            new = self.curdir + "/" + p
        else:
            new = p

        new = os.path.normpath(new).replace("\\", "/").replace("//", "/")

        d = self.afc.read_directory(new)
        if d:
            self.curdir = new
            self.prompt = "(AFC) %s " % new
        else:
            print "%s does not exist" % new

    def _complete(self, text, line, begidx, endidx):
        filename = text.split("/")[-1]
        dirname = "/".join(text.split("/")[:-1])
        return [dirname + "/" + x for x in self.afc.read_directory(self.curdir + "/" + dirname) if x.startswith(filename)]

    def do_ls(self, p):
        d = self.afc.read_directory(self.curdir + "/" + p)
        l = ""
        if d:
            for dd in d:
                l += "\n" + dd
        return l[1:]

    def do_cat(self, p):
        data = self.afc.get_file_contents(self.curdir + "/" + p)
        if data and p.endswith(".plist"):
            return parsePlist(data)
        else:
            return data

    def do_rm(self, p):
        self.afc.remove_path(self.curdir + "/" + p)

    def do_pull(self, p):
        t = p.split()
        data = self.afc.get_file_contents(self.curdir + "/" + t[0])
        if data and t[0].endswith(".plist"):
            z = parsePlist(data)
            plistlib.writePlist(z, os.path.basename(t[0]))
        else:
            if len(t) == 2:
                open(t[1], "wb").write(data)
            else:
                open(os.path.basename(t[0]), "wb").write(data)

    def do_push(self, p):
        t = p.split()
        if len(t) != 2:
            return
        data = open(t[1], "rb").read()
        self.afc.set_file_contents(self.curdir + "/" + t[0], data)

    def do_hexdump(self, p):
        t = p.split()
        l = 0
        if len(t) < 1:
            return
        if len(t) == 2:
            l = int(t[1])
        z = self.afc.get_file_contents(self.curdir + "/" + t[0])
        if not z:
            return
        if l:
            z = z[:l]
        return hexdump(z)

    def do_mkdir(self, p):
        return self.afc.make_directory(p)

    def do_infos(self, p):
        return self.afc.get_device_infos()

    def do_rmdir(self, p):
        return self.afc.remove_directory(p)

    def do_mv(self, p):
        t = p.split()
        return self.afc.rename_path(t[0], t[1])

    def do_about(self, p):
        return self.afc.get_file_info(p)

if __name__ == "__main__":
    """
    lockdown = LockdownClient()
    afc = AFCClient(lockdown)
    afc.read_directory("/DCIM/100APPLE/")
    d = afc.get_file_contents("/DCIM/100APPLE/IMG_0001.JPG")
    open("test.jpg","wb").write(d)
    afc.set_file_contents("/test.txt", "hello world")
    print afc.get_file_info("/etc/fstab")
    """
    AFCShell().cmdloop("Hello")
