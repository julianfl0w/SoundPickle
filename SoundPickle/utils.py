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


def convertUnknown(dirname, overwrite=False):
    if os.path.isfile(dirname):
        convertFile(os.path.abspath(dirname), overwrite=overwrite)
    else:
        for f in os.listdir(dirname):
            fullfilename = os.path.join(dirname, f)
            convertUnknown(fullfilename, overwrite=overwrite)

def convertFile(filename, overwrite=False, stopOnFail = True):
    if filename.endswith(".sfz") or filename.endswith(".sf2"):
            
        print("converting " + filename)
        # sfz objects return a single instrument
        if filename.endswith(".sfz"):

            outFilename = filename[:-4] + ".json"
            # dont overwrite if not requested
            if (not overwrite) and os.path.exists(outFilename):
                return 
            
            preprocParams = getParams(filename)
            try:
                spObj = sp.sound_pickle.fromSfz(filename = filename, **preprocParams)
            except Exception as e:
                print("couldnt process " + filename)
                raise(e)
            
            asDict = spObj.toJsonDict()
            with open(outFilename, 'w+') as f:
                #f.write(str(asDict))
                f.write(json.dumps(asDict, indent=2))
    
        # sf2 objects will return a list
        if filename.endswith(".sf2"):
            preprocParams = getParams(filename)

            if stopOnFail:
                    spObj = sp.sound_pickle.fromSf2(filename = filename, **preprocParams)
            else:
                try:
                    spObj = sp.sound_pickle.fromSf2(filename = filename, **preprocParams)
                except:
                    print("couldnt process " + filename)
                    return
            newdir = filename[:-4]
            os.makedirs(newdir, exist_ok=True)
            for i in spObj: 
                if i.name == "EOI":
                    continue
                outFilename = os.path.join(newdir, i.name + ".json")

                #os.makedirs(os.path.basename(outFilename), exist_ok=True)

                # dont overwrite if not requested
                if (not overwrite) and os.path.exists(outFilename):
                    return 
                del i.apex

                asDict = i.toJsonDict()
                with open(outFilename, 'w+') as f:
                    #f.write(str(asDict))
                    f.write(json.dumps(asDict, indent=2))
        

def flattenDict(d):
    retlist = []
    if type(d) == dict:
        for k, v in d.items():
            retlist += flattenDict(v)
    elif type(d) == list:
        raise Exception("No lists allowed")
    else:
        retlist += [d]
    return retlist


def getPatchesFromSf2(filename):
    retdict = {}
    with open(filename, "rb") as sf2_file:
        print("reading " + filename)
        sf2 = Sf2File(sf2_file)
        for inst in sf2.instruments:
            if inst.name == "EOI":
                continue

            inst.name = inst.name.replace("/", "_")
            print(inst.name)

            instpkl = filename + "." + inst.name + ".pkl"
            if os.path.exists(instpkl):
                with open(instpkl, "rb") as f:
                    retdict[inst.name] = pickle.load(f)

            else:
                retdict[inst.name] = SamplePatch(
                    displayName=inst.name, filename=instpkl
                )
                with open(instpkl, "wb+") as f:
                    pickle.dump(retdict[inst.name], f)
                args = {
                    "displayName": filename.replace(".sfz", ""),
                    "filename": filename,
                }

                with open(pklpatch, "wb+") as f:
                    pickle.dump(retdict[inst.name], f)

    return retdict

def getPatchFilenames(directory):

    retlist = []
    for file in os.listdir(directory):
        fullfile = os.path.join(directory, file)

        if os.path.isdir(fullfile):
            retlist += getPatchFilenames(fullfile)

        elif os.path.isfile(fullfile):
            if fullfile.endswith(".sp"):
                retdict += fullfile

    return retdict


def getPatchesFromDir(directory):

    retdict = {}
    for file in os.listdir(directory):
        fullfile = os.path.join(directory, file)

        if os.path.isdir(fullfile):
            retdict[file] = getPatchesFromDir(fullfile)
        elif os.path.isfile(fullfile):
            if fullfile.endswith(".sp"):
                #print(fullfile)
                try:
                    with open(fullfile, "rb") as f:
                        newObj = pickle.load(f)
                        newObj.soundPickleFilename = fullfile
                        retdict[file] = newObj
                except Exception as e: # work on python 3.x
                    print('Failed to open: '+ str(e))
                    print("couldn't open " + fullfile)

    return retdict
