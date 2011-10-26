#Copyright Jon Berg , turtlemeat.com

import os
import re
import cgi
import time
import mimetypes
from os import curdir, sep
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
                f = open(curdir + sep + self.path) #self.path has /test.html
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
        global rootnode
        url_handler = self.getHandler(self.path)
        if url_handler:
            return url_handler()
        try:
            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            if ctype == 'multipart/form-data':
                query=cgi.parse_multipart(self.rfile, pdict)
            else:
                self.send_error(500, 'POST with not multipart/form-data')
                return
            self.send_response(301)
            self.end_headers()
            upfilecontent = query.get('upfile')
            print "filecontent", upfilecontent[0]
            self.wfile.write("<HTML>POST OK.<BR><BR>");
            self.wfile.write(upfilecontent[0]);
        except Exception, e:
            print e.what()

    def addODG(self):
        print '>> addODG'
        content_type = self.headers.getheader('content-type')
        if content_type:
            ctype, pdict = cgi.parse_header(content_type)
            if ctype == 'multipart/form-data':
                print 'Found multipart/form-data'
                form = cgi.FieldStorage(self.rfile, self.headers)
                self.sendText('%s' % (form.filename))
                print form.filename
                return
            else:
                print 'Not multipart/form-data'
                self.send_error(500, 'POST with not multipart/form-data')
                return
        else:
            self.send_error(500, 'POST with no content-type')
            print 

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

