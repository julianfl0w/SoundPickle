


if __name__ == "__main__":

    p = patch.SamplePatch(
        displayName="Iconic EDM",
        filename=os.path.join(here, "../samples/EDM/Iconic_EDM_Leads.sf2"),
        volume=1,
        veloSensitive=True,
        normalize=True,
        attackLenSeconds=0.005,
        sustainLenSeconds=6,
        releaseLenSeconds=0.2,
        transpose=0,
        POLYPHONY=1,
        sf2inst=["Iconic EDM Lead"]
        # midiChannels = [0,1]
    )

    # p = patch.SamplePatch(
    #    displayName="Roland Steel Guitar",
    #    filename=os.path.join(
    #        here,
    #        "../samples/Top_12_Free_Guitar_Soundfonts/Guitar_Roland Steel Guitar.sf2",
    #    ),
    #    volume=1,
    #    veloSensitive=True,
    #    normalize=True,
    #    attackLenSeconds=0.005,
    #    sustainLenSeconds=6,
    #    releaseLenSeconds=0.2,
    #    transpose=0
    #    # midiChannels = [0,1]
    # )

    sfzInst = SF2Instrument(patch=p, platform_simple="debug", CHANNELS=1, cache=False)
