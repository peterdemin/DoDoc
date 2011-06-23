from import_uno import uno
import unohelper
import zipfile
import os

from com.sun.star.io import IOException, XOutputStream, XSeekable, XInputStream
from com.sun.star.beans import PropertyValue

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

class Document(file):
    def __init__(self, filename, mode='rb', buffering=1, delete_on_close=True):
        file.__init__(self, filename, mode, buffering)
        self.delete_on_close = delete_on_close

    def delete(self):
        os.unlink(self.name)

    def close(self):
        file.close(self)
        if self.delete_on_close:
            self.delete()

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
