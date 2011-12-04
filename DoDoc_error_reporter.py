#!usr/bin/python
# -*- coding: utf8 -*-
encoding='utf8'

import os
import sys
import smtplib
from email.mime.text import MIMEText
import DoDoc_inspector

def reportError(text):
    me = u'"DoDoc developer" <deminpe@otd263> (deminpe@otd263)'
    message = os.path.abspath(os.curdir)
    message+= u'\n\n'

    src_diff = DoDoc_inspector.hashDiff(os.path.join(os.path.dirname(__file__), 'dodoc_hashes.pkl'))
    if len(src_diff):
        message+= u'ATTENTION: Source changed:\n'
        message+= src_diff
    message+= u'\n\n'

    message+= u' '.join(sys.argv)
    message+= u'\n\n'

    message+= text.decode('cp866', 'replace')
    message = message.encode('utf8', 'replace')
    open("DoDoc_error.log", "wt").write(message)
    msg = MIMEText(message, 'plain', 'utf-8')
    msg['From']     = me.encode('utf8')
    msg['To']       = me.encode('utf8')
    msg['Subject']  = u'DoDoc traceback'.encode('utf8')
    try:
        import smtplib
        s = smtplib.SMTP()
        s.connect('mail.mars')
        s.sendmail(me, [me], msg.as_string())
        s.close()
    except (IOError, ImportError):
        # SMTP broken somehow
        pass
    sys.__stderr__.write(text)
