import sys
import os

here = os.path.dirname(os.path.abspath(__file__))
sys.path = [os.path.join(here, "sfzparser")] + sys.path
from .sfzparser import sfzparser
import math
import numpy as np
import json

sys.path.insert(0, os.path.join(here, "..", "..", "sinode"))
import sinode.sinode as sinode

def note2freq(note):
    a = 440.0  # frequency of A (common value is 440Hz)
    return (a / 32) * (2 ** ((note - 9) / 12.0))


class Region(sinode.Sinode):
    def __init__(self, **kwargs):
        sinode.Sinode.__init__(self, **kwargs)
        self.trimOffset = 0

        self.sampleMidiIndex = 57
        self.baseFrequency = 440
        if hasattr(self, "pitch_keycenter") and self.pitch_keycenter is not None:
            if type(self.pitch_keycenter) is int:
                self.sampleMidiIndex = self.pitch_keycenter
                self.baseFrequency = note2freq(self.pitch_keycenter)

            else:
                self.sampleMidiIndex = sfzparser.sfz_note_to_midi_key(
                    self.pitch_keycenter
                )
                self.baseFrequency = note2freq(
                    sfzparser.sfz_note_to_midi_key(self.pitch_keycenter)
                )

        # print(self.initDict)
        if (
            getattr(self, "loop_mode", None) == "loop_continuous"
        ):
            self.loop = True
            self.loopStart = int(int(self.loop_start))
            self.loopEnd = int(int(self.loop_end))

            self.loopLength = int(self.loop_end) - int(
                self.loop_start
            )

        else:
            self.loop = False
            self.loopStart = 0
            self.loopEnd = self.lengthSamples
            self.loopLength = 0

    def contains(self, msg, control):
        
        # randUnity = random.random()
        # if self.interface.DEBUG:
        #    randUnity = 0.5
        randUnity = 0.5
        randUnity = 0.5

        # Check for control change attributes with "_hicc" and "_locc" suffixes
        for attr_name in dir(self):

            if attr_name == "lovel" and msg.velocity < eval(attr_value):
                return False
            if attr_name == "hivel" and msg.velocity > eval(attr_value):
                return False
            if attr_name == "lorand" and randUnity < eval(attr_value):
                return False
            if attr_name == "hirand" and randUnity > eval(attr_value):
                return False
            
            if "_hicc" in attr_name:
                ccNum = int(attr_name.split("_hicc")[1])
                attr_value = getattr(self, attr_name)
                if control[ccNum] > int(attr_value):
                    return False

            elif "_locc" in attr_name:
                ccNum = int(attr_name.split("_locc")[1])
                attr_value = getattr(self, attr_name)
                if control[ccNum] < int(attr_value):
                    return False

            # if k.startswith("xfin_hicc"):
            #    return False
            # if k.startswith("xfin_locc"):
            #    return False
            # if k.startswith("xfout_hicc"):
            #    return False
            # if k.startswith("xfout_locc"):
            #    return False
        return True


    def optimizeLoop(self, y):
        if self.loop:

            periodLength = self.samplerate / self.baseFrequency
            print(periodLength)

            while self.loopStart % 2:
                self.loopStart += 1
            while self.loopEnd % 2:
                self.loopEnd += 1
            ogLen = 128
            halfOg = int(ogLen / 2)
            wholeLoop = y[self.loopEnd - ogLen : self.loopEnd]
            baseline = np.abs(np.fft.fft(wholeLoop))
            diff = math.inf
            mini = 0
            leadingHalf = y[self.loopEnd - halfOg : self.loopEnd]
            testLoop = np.append(leadingHalf, leadingHalf)
            for i in range(int(periodLength)):

                testLoop[halfOg:] = y[self.loopStart - i : self.loopStart - i + halfOg]
                thisSpec = np.abs(np.fft.fft(testLoop))
                thisdiff = np.sum(np.square(thisSpec - baseline))
                print("   diff")
                print("   " + str(diff))
                if thisdiff < diff:
                    diff = thisdiff
                    mini = i

            self.loopStart -= mini

            # look for the next upward zero cross
            # while(self.loopStart < self.loopEnd - periodLength):
            #    print("searching 0")
            #    if y[self.loopStart] < 0 and y[self.loopStart+1] >=0:
            #        break
            #    self.loopStart += 1
            #
            ## look for the next upward zero cross
            # while(self.loopEnd < self.lengthSamples - periodLength):
            #    print("searching 1")
            #    if y[self.loopEnd-1] < 0 and y[self.loopEnd] >=0:
            #        break
            #    self.loopEnd += 1

            self.loopLength = self.loopEnd - self.loopStart

            # make sure its a multiple of the base frequency
            unityFrequency = self.baseFrequency / self.samplerate
            loopLenClosest = int(self.loopLength / periodLength)

    def release(self):
        pass
