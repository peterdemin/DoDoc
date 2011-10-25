#Copyright Jon Berg , turtlemeat.com

import os
import re
import cgi
import time
import mimetypes
from os import curdir, sep
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print self.path
        try:
            for pattern, handler in self.handlers.iteritems():
                m = pattern.match(self.path)
                if m:
                    return handler(self, m.groups())
            if self.path == "/favicon.ico":
                self.send_response(200)
                self.send_header('Content-type',	'image/vnd.microsoft.icon')
                self.end_headers()
                self.wfile.write(open('favicon.ico', 'rb').read())
                return
            if self.path.endswith(".html"):
                f = open(curdir + sep + self.path) #self.path has /test.html
                self.send_response(200)
                self.send_header('Content-type',	'text/html')
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
                return
            if self.path.endswith(".esp"):   #our dynamic content
                self.send_response(200)
                self.send_header('Content-type',	'text/html')
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
        try:
            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            if ctype == 'multipart/form-data':
                query=cgi.parse_multipart(self.rfile, pdict)
            self.send_response(301)
            
            self.end_headers()
            upfilecontent = query.get('upfile')
            print "filecontent", upfilecontent[0]
            self.wfile.write("<HTML>POST OK.<BR><BR>");
            self.wfile.write(upfilecontent[0]);
            
        except :
            pass

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

