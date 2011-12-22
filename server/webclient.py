import os
import httplib
import mimetypes
import urlparse
from pprint import pprint
import json
import urllib2

def postForm_data(url, fields, files):
    """
    Post fields and files to an http host as multipart/form-data.
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return the server's response page.
    """
    host, selector = urlparse.urlsplit(url)[1:3]
    content_type, body = composeForm_data(fields, files)
    h = httplib.HTTP(host)
    h.putrequest('POST', selector)
    h.putheader('content-type', content_type)
    h.putheader('content-length', str(len(body)))
    h.endheaders()
    h.send(body)
    errcode, errmsg, headers = h.getreply()
    return h.file.read()

def postComposed(url, data):
    host, selector = urlparse.urlsplit(url)[1:3]
    content_type, body = data
    h = httplib.HTTP(host)
    h.putrequest('POST', selector)
    h.putheader('content-type', content_type)
    h.putheader('content-length', str(len(body)))
    h.endheaders()
    h.send(body)
    errcode, errmsg, headers = h.getreply()
    return h.file.read()

def composeForm_data(fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """
    BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = '\n'
    L = []
    for (key, value) in fields:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"' % key)
        L.append('')
        L.append(value)
    for (key, filename, value) in files:
        L.append('--' + BOUNDARY)
        L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
        L.append('Content-Type: %s' % getContent_type(filename))
        L.append('')
        L.append(value)
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body

def getContent_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

filenames = ['navig.odg',
             'bshv000_SpkRG.odg',
             'bshv001_SpkRG.odg',
             'bshv010_SpkRG.odg',
             'bshv020_SpkRG.odg',
             'koi_h.odg',
            ]

#session = json.loads(postForm_data('http://127.0.0.1/add/', [], [('upfile', name, open(name, 'rb').read()) for name in filenames]))

for i in range(10):
    #trash = urllib2.urlopen('http://www.mars/asu/index.html').read()
    trash = urllib2.urlopen('http://localhost/ping/').read()
    print 'ping'

datas = []
for filename in filenames:
    datas.append(composeForm_data([], [('upfile', filename, open(filename, 'rb').read())]))
    print '.',
print

session = {}
for data in datas:
    cur_session = json.loads(postComposed('http://127.0.0.1/add/', data))
    #session.update(cur_session)
    #pprint(cur_session)
command = {'template' : 'TT.odt', 'xml' : 'koi_h_TT.xml'}
result = json.loads(postForm_data('http://127.0.0.1/dodoc/', [('session', json.dumps(session)), ('command', json.dumps(command))], []))
pprint(result)
open('result.odt', 'wb').write(urllib2.urlopen('http://127.0.0.1/' + result['odt']).read())
os.startfile('result.odt')
