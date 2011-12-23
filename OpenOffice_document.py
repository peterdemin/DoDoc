from import_uno import uno
import unohelper
import zipfile
import os
from com.sun.star.io import IOException, XOutputStream, XSeekable, XInputStream
from com.sun.star.beans import PropertyValue
from com.sun.star.connection import NoConnectException

def progress(message):
    #if type(message) == unicode:
    #    print message.encode('cp866', 'replace')
    #else:
    #    print message
    pass

def error(message):
    import sys
    if type(message) == unicode:
        message = message.encode('cp866', 'replace')
    sys.__stderr__.write(message)
    raise Exception(message)

class OpenOffice(object):
    def __init__(self):
        self.component_context = uno.getComponentContext()
        self.url_resolver = self.component_context.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver', self.component_context)
        self.connected_context = None
        self.service_started_by_me = False

    def setConnection(self, connected_context):
        self.connected_context = connected_context
        unosvcmgr = self.connected_context.ServiceManager
        self.desktop    = unosvcmgr.createInstanceWithContext('com.sun.star.frame.Desktop',         self.connected_context)
        self.dispatcher = unosvcmgr.createInstanceWithContext('com.sun.star.frame.DispatchHelper',  self.connected_context)

    def connection(self):
        return self.connected_context

    def connect(self, port=2002):
        start_attempted = False
        connection_attempts = 0
        connected_context = None
        while not connected_context:
            try:
                progress('Attempting to connect...')
                connection_attempts+= 1
                url = 'uno:socket,host=localhost,port=%d;urp;StarOffice.ComponentContext' % (port)
                progress('Resolve "%s"' % (url))
                connected_context = self.resolveURL(url)
                progress('Connected.')
            except NoConnectException, e:
                progress('Connection failed.')
                if start_attempted:
                    if connection_attempts < 20:
                        import time
                        time.sleep(1.0)
                        progress('Waiting 1 second.')
                    else:
                        error('soffice service started, but connection could not be made.')
                else:
                    progress('Starting service...')
                    if self.startService(port):
                        start_attempted = True
                    else:
                        return False
        self.setConnection(connected_context)
        return True

    def disconnect(self):
        if self.service_started_by_me:
            self.stopService()

    def open(self, filename):
        try:
            instream = InputStream(uno.ByteSequence(open(filename, 'rb').read()))
            inputprops = [
                PropertyValue('InputStream', 0, instream, 0),
                PropertyValue('Hidden', 0, True, 0),
            ]
            self.doc = self.desktop.loadComponentFromURL('private:stream', '_blank', 0, tuple(inputprops))
            progress('Opened document "%s"' % (filename))
            return True
        except IOError, e:
            error(u'Error: Can not open input file: "%s"' % (os.path.abspath(filename)))
            return False

    def close(self):
        #progress('Attempting to close...')
        #self.doc.close(True) # what means True?
        progress('Attempting to dispose...')
        self.doc.dispose()
        progress('Disposed document.')
        pass

    def startService(self, port):
        import subprocess
        try:
            popen_arg = ['soffice', '-headless', '-nofirststartwizard', '-accept="socket,host=localhost,port=%d;urp;"' % (port)]
            progress('Start "%s"' % (popen_arg))
            soffice = subprocess.Popen(popen_arg)
            if None == soffice.poll():
                self.service_started_by_me = True
                progress('Service polled ok')
                return True
            else:
                error('Error: soffice process terminated unexpectadly.')
                return False
        except OSError, e:
            error('Error: Can not start soffice (probably system path not set properly)')
            return False

    def stopService(self):
        progress('Attempting to terminate soffice...')
        try:
            self.desktop.terminate()
            progress('soffice terminated.')
        except:
            progress('soffice termination failed.')

    def resolveURL(self, url):
        return self.url_resolver.resolve(url)

class InputStream(XSeekable, XInputStream, unohelper.Base):
      def __init__(self, seq):
          self.s = uno.ByteSequence(seq)
          self.nIndex = 0
          self.closed = 0

      def closeInput(self):
          self.closed = 1
          self.s = None

      def skipBytes(self, nByteCount):
          if(nByteCount + self.nIndex > len(self.s)):
              nByteCount = len(self.s) - self.nIndex
          self.nIndex += nByteCount

      def readBytes(self, retSeq, nByteCount):
          nRet = 0
          if(self.nIndex + nByteCount > len(self.s)):
              nRet = len(self.s) - self.nIndex
          else:
              nRet = nByteCount
          retSeq = uno.ByteSequence(self.s.value[self.nIndex : self.nIndex + nRet ])
          self.nIndex = self.nIndex + nRet
          return nRet, retSeq

      def readSomeBytes(self, retSeq , nByteCount):
          #as we never block !
          return readBytes(retSeq, nByteCount)

      def available(self):
          return len(self.s) - self.nIndex

      def getPosition(self):
          return self.nIndex

      def getLength(self):
          return len(self.s)

      def seek(self, pos):
          self.nIndex = pos

class OutputStream(unohelper.Base, XOutputStream):
    def __init__(self, descriptor=None):
        self.descriptor = descriptor
        self.closed = 0

    def closeOutput(self):
        self.closed = 1
        if not self.descriptor.isatty:
            self.descriptor.close()

    def writeBytes(self, seq):
        self.descriptor.write(seq.value)

    def flush(self):
        pass

def getTree(path):
    result = []
    items = os.listdir(path)
    for item in items:
        item_path = '/'.join([path, item])
        if os.path.isfile(item_path):
            result.append(item)
        elif os.path.isdir(item_path):
            result.append(item + '/')
            result.extend(['/'.join([item, a]) for a in getTree(item_path)])
    return result

def extractAll(zip_path, output_path):
    fd = zipfile.ZipFile(zip_path, 'r')
    for info in fd.infolist():
        dst_path = os.path.join(output_path, info.filename)
        if info.filename.endswith('/'):
            if not os.path.exists(dst_path):
                os.makedirs(dst_path)
        else:
            dst_dir_path = os.path.dirname(dst_path)
            if 0:
                if dst_dir_path != dst_path:
                    if not os.path.exists(dst_dir_path):
                        os.makedirs(dst_dir_path)
            fd.extract(info.filename, output_path)
    fd.close()
    return

def packAll(input_path, zip_path):
    fd = zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED)
    for name in getTree(input_path):
        src_path = os.path.join(input_path, name)
        if name.endswith('/'):
            fd.writestr(name, '')
        else:
            fd.write(src_path, name)
    fd.close()
    return
