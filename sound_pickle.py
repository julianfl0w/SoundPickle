import os
import sys
import pickle
from pedalboard import Pedalboard, Compressor
from sf2utils.sf2parse import Sf2File
import numpy as np
from pedalboard import *
import librosa
import copy 
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, ".."))
sys.path.insert(0, os.path.join(here, "..", "..", "sinode"))
import sinode.sinode as sinode
import SoundPickle as sp
import io
from pydub import AudioSegment

def spill(obj):
    print("spilling " + str(obj))
    for a in dir(obj):
        if not a.startswith("__") and a != "raw_sample_data":
            val = eval("obj." + a)
            print("    " + a + ": " + str(val))

def fromPickle(filename):
    with open(filename, 'rb') as f:
        print("loading " + filename)
        a = pickle.load(f)
        a.soundPickleFilename = filename
    return a 

def fromFile(filename, displayName=""):
    if filename.endswith("sf2"):
        for p in fromSf2(filename):
            if displayName == p.displayName:
                return p
    if filename.endswith("sfz"):
        return fromSfz(filename)


def fromSf2(filename, **kwargs):
    print("sf2 processing file " + filename)

    retlist = []

    with open(filename, "rb") as sf2_file:
        print(filename)
        sf2file = Sf2File(sf2_file)

        for i in sf2file.instruments:
            newObj = SoundPickle(sf2Inst = i, filename = filename, **kwargs)
            del newObj.sf2Inst
            retlist += [newObj]

    print("done processing samples")
    return retlist

def fromSfz(filename, **kwargs):
    return SoundPickle(filename = filename, **kwargs)

class SoundPickle(sinode.Sinode):
    def __init__(self, **kwargs):
        sinode.Sinode.__init__(self, **kwargs)
        self.proc_kwargs(
            compress = False,
            percussion = False,
            loop = True
        )
        
        if self.filename.endswith(".sfz"):
            self.displayName = os.path.basename(self.filename)[:-4]
            self.procSfz()

        elif self.filename.endswith(".sf2"):
            self.source = "sf2"
            self.displayName = self.sf2Inst.name
            self.name = self.sf2Inst.name

            self.percussiveSampleIndex = 45
            self.binaryBlob = np.zeros((0), dtype=np.float32)

            self.regions = []
            self.sample2region = {}
            # spill(i)
            if hasattr(self.sf2Inst, "bags"):
                # print("bags")
                for bag in self.sf2Inst.bags:
                    # spill(bag)
                    if hasattr(bag, "sample") and bag.sample is not None:
                        self.processSample(bag.sample)
                # die\
        else:
            raise Exception("Unimplemented filetype " + self.filename)


    def procSfz(self):
        self.source = "sfz"
        self.filenameBasedir = os.path.dirname(self.filename)
        self.samplesLoadPoint = self.filenameBasedir
        self.binaryBlob = np.zeros((0), dtype=np.float32)

        startAddr = 0

        # self.samples2bin() # read the samples
        print("loading from " + str(self.filename))
        processedText = self.preprocessSfz(self.filename)
        with open("a.spz", "w+") as f:
            f.write(processedText)

        sfzParser = sp.sfzparser.sfzparser.SFZParser("a.spz")
        # pprint.pprint(sfzParser.sections)

        self.regions = []
        self.globalDict = {}
        self.masterDict = {}
        self.groupDict = {}

        sample2region = {}

        for sectionName, valueDict in sfzParser.sections:
            # print(sectionName)
            # print(valueDict)

            if sectionName == "region":
                # add all the global items
                for k, v in self.groupDict.items():  # GROUP
                    if k not in valueDict.keys():
                        valueDict[k] = v
                for k, v in self.masterDict.items():  # MASTER
                    if k not in valueDict.keys():
                        valueDict[k] = v
                for k, v in self.globalDict.items():  # GLOBAL
                    if k not in valueDict.keys():
                        valueDict[k] = v

                # resolve sample path
                resolved =  os.path.join(self.samplesLoadPoint, valueDict["sample"])
                
                valueDict["sample"] = resolved

                if not resolved in sample2region.keys():
                    print("sfz processing " + resolved)
                    if not os.path.exists(resolved):
                        print("file does not exist. skipping")
                        continue

                    # Read in a whole audio file:
                    y, samplerate = librosa.load(resolved)
                    y = self.audioProcess(y, samplerate)

                    valueDict["addressInPatch"] = startAddr
                    valueDict["lengthSamples"] = len(y)
                    valueDict["sample_rate"] = samplerate

                    newRegion = sp.region.Region(valueDict)
                    # newRegion.optimizeLoop(y)

                    if len(np.shape(y)) == 1:
                        channelCount = 1
                    else:
                        channelCount = np.shape(y)[1]

                    newRegion.channelCount = channelCount
                    for channel in range(channelCount):
                        self.binaryBlob = np.append(self.binaryBlob, y, axis=0)
                        newRegion.sampleFilenameAndChannel = (
                            resolved + "_" + str(channel)
                        )
                    startAddr += len(y)
                    sample2region[resolved] = newRegion

                else:
                    newregion = copy.deepcopy(sample2region[resolved])
                self.regions += [newRegion]

            elif sectionName == "global":
                self.globalDict = valueDict

            elif sectionName == "master":
                self.masterDict = valueDict

            elif sectionName == "group":
                self.groupDict = valueDict
                # print(json.dumps(valueDict, indent=2))
 
            elif sectionName == "control":
                for k, v in valueDict.items():
                    if k == "default_path" or k == "prefix_sfz_path":
                        v = v.replace("\\", os.sep)
                        self.samplesLoadPoint = os.path.join(self.filenameBasedir, v)
                        print("Changing load point to " + str(self.samplesLoadPoint))

            elif sectionName == "comment":
                pass

            elif sectionName == "curve":
                pass
            elif sectionName == "":
                pass
            else:
                raise Exception("Unknown sfz header '" + str(sectionName) + "'")

        # save binary file for reloading
        if not len(self.regions):
            raise Exception("Empty regions list")

    def preprocessSfz(self, filename, replaceDict={}):
        print("processing file " + str(filename))
        # read in the template sfz
        with open(filename, "r") as f:
            preprocFile = f.read()

        preProcessText = ""
        for ogline in preprocFile.split("\n"):
            ogline = ogline.strip()
            line = ogline.split("//")[0]
            for k, v in replaceDict.items():
                line = line.replace(k, v)

            # keep the comments
            if ogline.startswith("//"):
                preProcessText += ogline

            if "#include" in line:
                includeParts = line.split("#include")[1:]
                print(includeParts)
                for i, includePart in enumerate(includeParts):
                    includePart = includePart.strip()
                    includeFilename = eval(
                        includePart.split(" ")[0]
                    )  # NO SPACES ALLOWED IN FILENAMES!
                    includeFilename = os.path.join(
                        self.filenameBasedir, includeFilename
                    )
                    includeText = self.preprocessSfz(
                        includeFilename, replaceDict=replaceDict.copy()
                    )
                    preProcessText += "\n" + includeText + "\n"

            elif line.startswith("#define"):
                preProcessText += line
                k = line.split(" ")[1]
                v = "".join(line.split(" ")[2:])
                replaceDict[k] = v
            else:
                preProcessText += line

            preProcessText += "\n"

        return preProcessText


    def noteInSfzRegion(self, noteNo, region):
        if self.source == "sf2":
            return noteNo == region.pitch_keycenter
        
        inRegion = True
        if "lokey" in region.initDict.keys() and noteNo < sp.sfzparser.sfzparser.sfz_note_to_midi_key(
            region.lokey
        ):
            inRegion = False
        if "hikey" in region.initDict.keys() and noteNo > sp.sfzparser.sfzparser.sfz_note_to_midi_key(
            region.hikey
        ):
            inRegion = False
        return inRegion

  

        # pp.pprint(sf2file.presets)
        # for bag in sf2file.presets:
        #    pp.pprint(bag)
        # for bag in sf2file.instruments:
        #    pp.pprint(bag)
        #    print(dir(s))
        #    print(s.DEFAULT_PITCH)
        #    print(s.start)
        #    print(s.end)
        #    print(s.sample_width)
        #    print(s.CHANNEL_MONO)
        #    print(s.raw_sample_data)

    def audioProcess(self, sampleData, sample_rate):
        
        # fade in the first 32 samples
        sampleData[:32] *= np.arange(32) / 32

        return sampleData
    
    def processSample(self, sample):

        print("sf2 processing " + sample.name)
        # if not hasattr(sample, "start"):
        #    return

        if sample.name in self.sample2region.keys():
            thisregion = self.sample2region[sample.name]  # .copy()
            return

        for a in dir(sample):
            if not a.startswith("__") and a != "raw_sample_data":
                val = eval("sample." + a)
                print("    " + a + ": " + str(val))

        # read in the data
        newData = np.frombuffer(sample.raw_sample_data, dtype=np.int16).astype(
            np.float32
        ) / (2 ** 16)
        newData = self.audioProcess(newData, sample_rate = sample.sample_rate)

        # print(sample.sample_type)
        regionDict = {
            "sample_rate": sample.sample_rate,
            "sample": sample.name,
            "addressInPatch": len(self.binaryBlob),
            "lengthSamples": len(newData),
        }

        # if the sample has original_pitch attribute, use that
        if hasattr(sample, "original_pitch"):
            regionDict["pitch_keycenter"] = int(sample.original_pitch)
        else:
            regionDict["pitch_keycenter"] = int(sample.name)

        if self.percussion:
            regionDict["pitch_keycenter"] = self.percussiveSampleIndex
            self.percussiveSampleIndex += 1

        print(regionDict["pitch_keycenter"])

        if hasattr(sample, "start_loop") and self.loop:
            if sample.start_loop < sample.start:
                regionDict.update(
                    {
                        "loop_start": sample.start_loop,
                        "loop_end": sample.end_loop,
                        "loop": 1,
                        "loop_mode": "loop_continuous",
                    }
                )

            else:
                regionDict.update(
                    {
                        "loop_start": sample.start_loop - sample.start,
                        "loop_end": sample.end_loop - sample.start,
                        "loop": 1,
                        "loop_mode": "loop_continuous",
                    }
                )

        thisregion = sp.region.Region(regionDict)
        # print(regionDict)

        self.binaryBlob = np.append(self.binaryBlob, newData, axis=0)

        thisregion.samplesLoadPoint = ""
        self.sample2region[sample.name] = thisregion

        self.regions += [thisregion]

def convertDirectory():
    if len(sys.argv) != 2:
    	raise Exception("Usage: soundpickle directory")
    directory = sys.argv[1]
    print("Converting directory " + directory )
    sp.utils.convertUnknown(directory)

if __name__ == "__main__":
    convertDirectory()
