import os
import sys
import pickle
here = os.path.dirname(__file__)
sys.path.insert(0,os.path.join(here, ".."))

import SoundPickle as sp

def convertFile(filename, overwrite=False):
    if filename.endswith(".sfz") or filename.endswith(".sf2"):

        # dont overwrite if not requested
        outfilename = filename + ".sp"
        if (not overwrite) and os.path.exists(outfilename):
            return 
        
        print("converting " + filename)
        spObj = sp.sound_pickle.SoundPickle(filename = filename)
        
        print(spObj)
        
        with open(outfilename, 'wb+') as f:
            pickle.dump(spObj, f)

def convertDirectory(dirname, overwrite=False):
    for f in os.listdir(dirname):
        fullfilename = os.path.join(dirname, f)
        if os.path.isfile(fullfilename):
            convertFile(fullfilename, overwrite=overwrite)
        else:
            convertDirectory(fullfilename, overwrite=overwrite)
