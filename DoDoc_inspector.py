from hashlib import md5
from glob import glob
try:
    import cPickle as pickle
except ImportError:
    import pickle

def saveHashes(filename = 'dodoc_hashes.pkl'):
    hashes = {}
    for f in glob("*.py"):
        hashes[f] = md5(open(f, "rb").read()).hexdigest()
    pickle.dump(hashes, open(filename, 'wb'))

def isValid(filename = 'dodoc_hashes.pkl'):
    import os
    if os.path.exists(filename):
        hashes = pickle.load(open(filename, 'rb'))
        for f in glob("*.py"):
            cur_hash = md5(open(f, "rb").read()).hexdigest()
            if hashes.has_key(f):
                if hashes[f] == cur_hash:
                    continue
            return False
    return True

def main():
    saveHashes()
    print isValid()

if __name__ == '__main__':
    main()
