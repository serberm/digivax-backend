from ftplib import FTP_TLS, FTP
import ftplib
import socket
import ssl
import os
from flask import current_app

class ImplicitFTP_TLS(ftplib.FTP_TLS):
    """FTP_TLS subclass that automatically wraps sockets in SSL to support implicit FTPS."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sock = None

    @property
    def sock(self):
        """Return the socket."""
        return self._sock

    @sock.setter
    def sock(self, value):
        """When modifying the socket, ensure that it is ssl wrapped."""
        if value is not None and not isinstance(value, ssl.SSLSocket):
            value = self.context.wrap_socket(value)
        self._sock = value

    # from https://stackoverflow.com/questions/50115522/ftplib-storbinary-with-ftps-is-hanging-never-completing
    def storbinary(self, cmd, fp, blocksize=8192, callback=None, rest=None):
      self.voidcmd('TYPE I')
      #print('doing it')
      with self.transfercmd(cmd, rest) as conn:
        while 1:
          buf = fp.read(blocksize)
          if not buf: break
          conn.sendall(buf)
          if callback: callback(buf)
        # shutdown ssl layer
        if isinstance(conn, ssl.SSLSocket):
          # HACK: Instead of attempting unwrap the connection, pass here
          pass
      return self.voidresp()

    def reconnect(self):
        self.connect(host=current_app.config["USLABS_SFTP_HOST"], port=current_app.config["USLABS_SFTP_PORT"])
        self.login(user=current_app.config["USLABS_SFTP_USER"], passwd=current_app.config["USLABS_SFTP_PASS"])
        self.prot_p()

ftps = ImplicitFTP_TLS()

def make_directory(ftps, thisdir, newdir):

    ftps.cwd(thisdir)

    if newdir not in ftps.nlst():
        ftps.mkd(newdir)

def send_files(ftps, path):

    files = os.listdir(path)
    os.chdir(path)
    #print(os.getcwd())
    #print(files)
    for f in files:
        #pdb.set_trace()
        #print(f)
        if os.path.isfile(path + '/'+f):
            #print('here')
            # check that doesnt exist. if it does delete and reupload
            #pdb.set_trace()
            fh = open(f, 'rb')
            ftps.storbinary('STOR %s' % f, fh)
            fh.close()
        elif os.path.isdir(path + '/'+f):
            #print('or here')
            # check that doesnt exist. if it does delete and reupload
            if f not in ftps.nlst():
                ftps.mkd(f)
            ftps.cwd(f)
            send_files(ftps, path + '/'+f)
    ftps.cwd('..')
    os.chdir('..')

def send_just_files(ftps, path, ftps_dir):

    ftps.cwd(ftps_dir) 

    files = os.listdir(path)
    os.chdir(path)
    #print(os.getcwd())
    #print(files)
    for f in files:

        if f=='.gitignore':
            continue
        #pdb.set_trace()
        #print(f)
        if os.path.isfile(path + '/'+f):
            #print('here')
            # check that doesnt exist. if it does delete and reupload
            #pdb.set_trace()
            fh = open(f, 'rb')
            ftps.storbinary('STOR %s' % f, fh)
            fh.close()
        elif os.path.isdir(path + '/'+f):
            pass # dont recursively go through directories
    
    ftps.cwd('/')