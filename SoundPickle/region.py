import sys
import os

here = os.path.dirname(os.path.abspath(__file__))
sys.path = [os.path.join(here, "sfzparser")] + sys.path
print(sys.path)
from .sfzparser import sfzparser
import math
import numpy as np


def note2freq(note):
    a = 440.0  # frequency of A (common value is 440Hz)
    return (a / 32) * (2 ** ((note - 9) / 12.0))


class Region:
    def __init__(self, initDict):
        self.initDict = initDict
        # make the constants available locally
        for k, v in self.initDict.items():
            k = k.replace("#", "")
            if " " not in k:  # sometimes wierd stuff comes through
                if type(v) != str:
                    exec("self." + k + " = " + str(v))
                else:
                    exec("self." + k + ' = "' + v + '"')

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
            "loop_mode" in self.initDict.keys()
            and self.initDict["loop_mode"] == "loop_continuous"
        ):
            self.loop = True
            self.loopStart = int(int(self.initDict["loop_start"]))
            self.loopEnd = int(int(self.initDict["loop_end"]))

            self.loopLength = int(self.initDict["loop_end"]) - int(
                self.initDict["loop_start"]
            )

        else:
            self.loop = False
            self.loopStart = 0
            self.loopEnd = self.lengthSamples
            self.loopLength = 0

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
