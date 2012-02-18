from hashlib import md5
from glob import glob
import json

ignored = [r'upload_to_ftp.py']

def saveHashes(filename = 'dodoc_hashes.json'):
    hashes = {}
    for f in glob("*.py"):
        if f not in ignored:
            hashes[f] = md5(open(f, "rb").read()).hexdigest()
    json.dump(hashes, open(filename, 'wb'), sort_keys=True, indent=4)

def hashDiff(filename = 'dodoc_hashes.json'):
    import os
    diff = []
    if os.path.exists(filename):
        work_dir = os.path.dirname(__file__)
        hashes = json.load(open(filename, 'rb'))
        for f, hash in hashes.iteritems():
            filepath = os.path.join(work_dir, f)
            if os.path.exists(filepath):
                cur_hash = md5(open(filepath, "rb").read()).hexdigest()
                if hash == cur_hash:
                    continue
                else:
                    diff.append('M ' + f)
            else:
                diff.append('R ' + f)
    else:
        diff.append('R ' + filename)
    return '\n'.join(diff)

def main():
    import sys
    if len(sys.argv) == 2:
        if sys.argv[1] == '--save':
            saveHashes()
    else:
        print hashDiff()

if __name__ == '__main__':
    main()
