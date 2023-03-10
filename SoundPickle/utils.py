import os
import sys
import pickle
here = os.path.dirname(__file__)
sys.path.insert(0,os.path.join(here, ".."))

import SoundPickle as sp

def convertFile(filename, overwrite=False):
    if filename.endswith(".sfz") or filename.endswith(".sf2"):

        
        print("converting " + filename)
        # sfz objects return a single instrument
        if filename.endswith(".sfz"):
            spObj = sp.sound_pickle.fromSfz(filename = filename)
        
            print(spObj)
            
            # dont overwrite if not requested
            if (not overwrite) and os.path.exists(spObj.outFilename):
                return 
            
            with open(spObj.outFilename, 'wb+') as f:
                pickle.dump(spObj, f)
        
        # sf2 objects will return a list
        else:
            spObj = sp.sound_pickle.fromSf2(filename = filename)
        
            for i in spObj: 
                with open(i.outFilename, 'wb+') as f:
                    pickle.dump(i, f)
        

def convertDirectory(dirname, overwrite=False):
    for f in os.listdir(dirname):
        fullfilename = os.path.join(dirname, f)
        if os.path.isfile(fullfilename):
            convertFile(fullfilename, overwrite=overwrite)
        else:
            convertDirectory(fullfilename, overwrite=overwrite)
