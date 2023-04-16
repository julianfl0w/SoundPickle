import os
import sys
import pickle
import json
here = os.path.dirname(__file__)
sys.path.insert(0,os.path.join(here, ".."))

import SoundPickle as sp

def getParams(filename):
    # if no preprocess file is available, create it
    preprocessJson = filename + ".preprocess.json"
    print(preprocessJson)
    if not os.path.exists(preprocessJson):
        defaults = dict(
            compressDB = 40,
            compressRate = 4,
            compress = False,
            normalize = True,
            trimDB = 40,
            percussion = False,
            loop = True)
        with open(preprocessJson, 'w+') as f:
            f.write(json.dumps(defaults, indent=2))

    # open the preprocess file
    with open(preprocessJson, 'r') as f:
        preprocParams = json.loads(f.read())
    return preprocParams

def convertFile(filename, overwrite=False):
    if filename.endswith(".sfz") or filename.endswith(".sf2"):
            
        print("converting " + filename)
        # sfz objects return a single instrument
        if filename.endswith(".sfz"):

            outFilename = filename[:-4] + ".sp"
            # dont overwrite if not requested
            if (not overwrite) and os.path.exists(outFilename):
                return 
            
            preprocParams = getParams(filename)
            try:
                spObj = sp.sound_pickle.fromSfz(filename = filename, **preprocParams)
            except:
                print("couldnt process " + filename)
                return
            print(spObj)
            with open(outFilename, 'wb+') as f:
                pickle.dump(spObj, f)
        
        # sf2 objects will return a list
        else:
            preprocParams = getParams(filename)

            try:
                spObj = sp.sound_pickle.fromSf2(filename = filename, **preprocParams)
            except:
                print("couldnt process " + filename)
                return
            newdir = filename[:-4]
            os.makedirs(newdir, exist_ok=True)
            for i in spObj: 
                outFilename = os.path.join(newdir, i.name + ".sp")

                # dont overwrite if not requested
                if (not overwrite) and os.path.exists(outFilename):
                    return 
                
                with open(outFilename, 'wb+') as f:
                    pickle.dump(i, f)
        

def convertDirectory(dirname, overwrite=False):
    for f in os.listdir(dirname):
        fullfilename = os.path.join(dirname, f)
        if os.path.isfile(fullfilename):
            convertFile(fullfilename, overwrite=overwrite)
        else:
            convertDirectory(fullfilename, overwrite=overwrite)
