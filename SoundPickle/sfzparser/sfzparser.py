#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A parser for SFZ files."""

import math
import re
from pathlib import Path
import os
import sys
from collections import OrderedDict
import numpy as np
from io import open
import pickle
from tqdm import tqdm
import json
import librosa
from pedalboard.io import AudioFile
from pedalboard import *

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

import sound_pickle
import copy

SFZ_NOTE_LETTER_OFFSET = {"a": 9, "b": 11, "c": 0, "d": 2, "e": 4, "f": 5, "g": 7}


def sfz_note_to_midi_key(sfz_note, german=False):
    while sfz_note.startswith("0"):
        sfz_note = sfz_note[1:]
    accidental = 0

    if "#" in sfz_note[1:] or "♯" in sfz_note:
        accidental = 1
    elif "b" in sfz_note[1:] or "♭" in sfz_note:
        accidental = -1

    letter = sfz_note[0].lower()
    if letter.isdigit():
        return eval(sfz_note)

    if german:
        # TODO: Handle sharps (e.g. "Fis") and flats (e.g. "Es")
        if letter == "b":
            accidental = -1
        if letter == "h":
            letter = "b"

    octave = int(sfz_note[-1])
    midikey = max(
        0, min(127, SFZ_NOTE_LETTER_OFFSET[letter] + ((octave + 1) * 12) + accidental)
    )
    return midikey


def freq_to_cutoff(param):
    return 127.0 * max(0, min(1, math.log(param / 130.0) / 5)) if param else None


class SFZParser(object):
    rx_section = re.compile("^<([^>]+)>\s?")

    def __init__(self, sfz_path, encoding=None, **kwargs):
        self.encoding = encoding
        self.sfz_path = sfz_path
        self.groups = []
        self.sections = []

        with open(sfz_path, encoding=self.encoding or "utf-8-sig") as sfz:
            self.parse(sfz)

    def parse(self, sfz):
        section_name = ""
        sections = self.sections
        cur_section = []
        value = None

        for line in sfz:
            line = line.strip()

            if not line:
                continue

            if line.startswith("//"):
                sections.append(("comment", line))
                continue

            while line:
                match = self.rx_section.search(line)
                if match:
                    if cur_section:
                        sections.append(
                            (section_name, OrderedDict(reversed(cur_section)))
                        )
                        cur_section = []

                    section_name = match.group(1).strip()
                    line = line[match.end() :].lstrip()
                elif "=" in line:
                    line, _, value = line.rpartition("=")
                    if "=" in line:
                        line, key = line.rsplit(None, 1)
                        cur_section.append((key, value))
                        value = None
                elif value:
                    line, key = None, line
                    cur_section.append((key, value))
                else:
                    if line.startswith("//"):
                        print("Warning: inline comment")
                        sections.append(("comment", line))
                    # ignore garbage
                    break

        if cur_section:
            sections.append((section_name, OrderedDict(reversed(cur_section))))

        return sections


if __name__ == "__main__":
    import pprint
    import sys

    parser = SFZParser(sys.argv[1])
    pprint.pprint(parser.sections)
