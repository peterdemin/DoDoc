def findStarOffice():
    marker = 'Office'
    possible = filter(lambda a: a.find(marker) >= 0, os.environ['PATH'].split(';'))
    p = possible[0]
    dir_names = filter(len, p.split(os.sep))
    base_ooo_path_parts = []
    for d in dir_names:
        base_ooo_path_parts.append(d)
        if d.find(marker) >= 0:
            break
    return os.sep.join(base_ooo_path_parts) + os.sep

try:
    # On Linux, or OOo python
    import uno
except ImportError:
    # On Windows with installed python
    import os
    import sys

    ooo_path = findStarOffice()

    #ooo_path = r'C:\Program Files\OpenOffice.org 3\\'
    URE_BOOTSTRAP   = r'vnd.sun.star.pathname:' + ooo_path + r'program\fundamental.ini'
    UNO_PATH        = ooo_path + r'program\\'
    EXE_PATH        = ooo_path + r'URE\bin;' + ooo_path + r'Basis\program;'
    UNO_SCRIPT_PATH = ooo_path + r'Basis\program'

    os.environ['URE_BOOTSTRAP'] = URE_BOOTSTRAP
    os.environ['UNO_PATH'] = UNO_PATH
    os.environ['PATH'] = EXE_PATH + os.environ['PATH']
    sys.path.append(UNO_SCRIPT_PATH)

    try:
        import uno
    except ImportError:
        print 'I thought openoffice is at "%s", but it was mistake. Take a look at your PATH environment variable.' % (ooo_path)
