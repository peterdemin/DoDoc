import email.message
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import email.parser
import urllib2
import json

filename = 'koi_h.odg'

msg = MIMEMultipart()
payload = MIMEApplication(open(filename, 'rb').read())
payload.add_header('Content-Disposition', 'form-data', filename=filename, name='upfile')
msg.attach(payload)

headers, body = {}, ''
in_headers = True
for line in msg.as_string().splitlines():
    if in_headers:
        if len(line.strip()) == 0:
            in_headers = False
        else:
            item = line.split(':', 1)
            headers[item[0].strip()] = item[1].strip()
    else:
        body+= line + '\n'

from pprint import pprint
pprint(headers)
request = urllib2.Request('http://localhost/add/', headers=headers)
pprint( json.load(urllib2.urlopen(request, body)) )
