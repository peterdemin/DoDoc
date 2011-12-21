import os
import re
import cgi
import time
import mimetypes
import email.parser
import json
import hashlib
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

class Server_API(object):
    def __init__(self):
        pass

    def hasODG(self, filename):
        return os.path.exists(filename)

    def getODG(self, filename):
        if hasODG(filename):
            return open(filename, 'rb').read()
        return None

    def addODG(self, filename, content):
        try:
            basename = os.path.basename(filename)
            if not os.path.isdir(basename):
                os.mkdir(basename)
            open(os.path.join(basename, '.odg'), 'wb').write('content')
            return True
        except IOError, e:
            return False

class MyHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super(MyHandler, self).__init__(*args, **kwargs)
        self.api = Server_API()

    def getHandler(self, request_path):
        for pattern, handler in self.handlers.iteritems():
            m = pattern.match(request_path)
            if m:
                return lambda: handler(self, *m.groups())
        return None

    def do_GET(self):
        print self.path
        try:
            url_handler = self.getHandler(self.path)
            if url_handler:
                return url_handler()
            if self.path == "/favicon.ico":
                self.send_response(200)
                self.send_header('Content-type', 'image/vnd.microsoft.icon')
                self.end_headers()
                self.wfile.write(open('favicon.ico', 'rb').read())
                return
            if self.path.endswith(".html"):
                f = open(os.curdir + os.sep + self.path) #self.path has /test.html
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
                return
            if self.path.endswith(".esp"):   #our dynamic content
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write("hey, today is the" + str(time.localtime()[7]))
                self.wfile.write(" day in the year " + str(time.localtime()[0]))
                return
            return
        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)

    def sendText(self, text):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(text)

    def do_POST(self):
        print 'do_POST'
        url_handler = self.getHandler(self.path)
        if url_handler:
            url_handler()
        else:
            print 'Can NOT handle', self.path

    def addODG(self):
        size = int(self.headers['content-length'])
        content = 'content-type: %s\n\n' % (self.headers['content-type'])
        content+= self.rfile.read(size)
        open('request.txt', 'wb').write(content)
        message = email.parser.Parser().parsestr(content)
        payload = message.get_payload()
        new_filename = None
        self.send_response(200)
        self.end_headers()
        post_processing = []
        print '!'
        for part in payload:
            parameters = dict(filter(lambda b: len(b)==2, [a.strip().split('=') for a in part['Content-Disposition'].split(';')]))
            if parameters.has_key('name') and parameters['name'] == '"upfile"':
                filename = parameters['filename'].strip('"')
                basename, ext = os.path.splitext(filename)
                if ext.lower() == '.odg':
                    file_content = part.get_payload(decode=True)
                    new_filename = hashlib.md5(file_content).hexdigest()
                    if not os.path.exists(new_filename):
                        open(new_filename, 'wb').write(file_content)
                        post_processing.append({filename : new_filename})
        print len(post_processing)
        if len(post_processing):
            self.wfile.write(json.dumps(post_processing))
        else:
            self.wfile.write(json.dumps({'error' : 'no payload'}))
        self.wfile.flush()
        self.connection.shutdown(1)
        if len(post_processing):
            from DoDoc.odg2png import Odg2png
            result = None
            o = Odg2png()
            if o.connect():
                for origin, input in post_processing:
                    print input
                    if o.open(input):
                        output = input + '.png'
                        result = o.savePNG(output)
                        o.close()
            o.disconnect()

    def hasODG(self, params):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        if len(params) == 1:
            odg_md5 = params[0]
            print odg_md5
            if os.path.exists(odg_md5):
                self.wfile.write('yes')
                return
        self.wfile.write('no')
        return

    def getODG(self, params):
        if len(params) == 1:
            filename = params[0]
            if os.path.exists(filename):
                self.send_response(200)
                mime = mimetypes.guess_type(filename)[0] or 'text/plain'
                self.send_header('Content-type', mime)
                self.end_headers()
                self.wfile.write(open(filename, 'rb').read())
                return
        self.send_error(404, 'File Not Found: %s' % self.path)

    handlers = {
                re.compile(r'(?i)/has/([a-f0-9]{16}\.\w+)') : hasODG,
                re.compile(r'(?i)/get/([a-f0-9]{16}\.\w+)') : getODG,
                re.compile(r'(?i)/add/') : addODG,
               }

def main():
    try:
        server = HTTPServer(('', 80), MyHandler)
        print 'started httpserver...'
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()

if __name__ == '__main__':
    main()

