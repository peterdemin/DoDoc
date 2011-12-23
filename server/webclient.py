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
    return postComposed(url, composeForm_data(fields, files))

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

filenames = ['client-data/navig.odg',
             'client-data/bshv000_SpkRG.odg',
             'client-data/bshv001_SpkRG.odg',
             'client-data/bshv010_SpkRG.odg',
             'client-data/bshv020_SpkRG.odg',
             'client-data/koi_h.odg',
             'client-data/koi_h_TT.xml',
            ]

#session = json.loads(postForm_data('http://127.0.0.1/add/', [], [('upfile', name, open(name, 'rb').read()) for name in filenames]))

def ping():
    for i in range(3):
        print urllib2.urlopen('http://localhost/ping/').read()
    print urllib2.urlopen('http://localhost/shutdown/').read()

#ping()

def main():
    server_host = 'http://127.0.0.1:8080'

    #filename = 'client-data/bshv000_SpkRG.odg'
    #data = composeForm_data([], [('upfile', os.path.basename(filename), open(filename, 'rb').read())])
    #print json.loads(postComposed(server_host + '/add/', data))
    #return

    datas = []
    for filename in filenames:
        datas.append(composeForm_data([], [('upfile', os.path.basename(filename), open(filename, 'rb').read())]))
        print '.',
    print

    session = {}
    for data in datas:
        cur_session = json.loads(postComposed(server_host + '/add/', data))
        session.update(cur_session)
    command = {'template' : 'TT.odt', 'xml' : 'koi_h_TT.xml'}
    result = json.loads(postForm_data(server_host + '/dodoc/', [('session', json.dumps(session)),
                                                                ('command', json.dumps(command))],
                                      []))
    pprint(result)
    open('client-data/result.odt', 'wb').write(urllib2.urlopen(server_host + '/' + result['odt']).read())
    os.startfile(r'client-data\result.odt')

if __name__ == '__main__':
    main()
