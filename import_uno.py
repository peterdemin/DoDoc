import os
import sys

URE_BOOTSTRAP   = r'vnd.sun.star.pathname:C:\Program Files\OpenOffice.org 3\program\fundamental.ini'

UNO_PATH        = r'C:\Program Files\OpenOffice.org 3\program\\'

EXE_PATH        = r'C:\Program Files\OpenOffice.org 3\URE\bin;C:\Program Files\OpenOffice.org 3\Basis\program;'

UNO_SCRIPT_PATH = r'C:\Program Files\OpenOffice.org 3\Basis\program'

os.environ['URE_BOOTSTRAP'] = URE_BOOTSTRAP
os.environ['UNO_PATH'] = UNO_PATH
os.environ['PATH'] = EXE_PATH + os.environ['PATH']
sys.path.append(UNO_SCRIPT_PATH)

import uno
