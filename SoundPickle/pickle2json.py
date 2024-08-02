import os
import sys
import json
here = os.path.dirname(__file__)
sys.path.insert(0,os.path.join(here, ".."))
import sound_pickle as sp

def pickle2json(filename):
    a = sp.fromPickle(filename)
    with open(filename[:-3] + ".json", 'w+') as f:
        f.write(json.dumps(a.toJsonDict(), indent=2))

if __name__ == "__main__":
    pickle2json(sys.argv[1])
