import os
billboard_home = "../Data/McGill billboard project/McGill-Billboard"

def read_billboard_songs():
    """
    read the billboard song chords dataset, and return a dictionary, where the keys
    are (song_title,artist) tuples, and the values are tuples of the song starting
    tonic and its chord vector.

    The dataset is formatted in directories, where each directory contains two files
    with data on one song.

    The "salami_chords.txt" file contains SALAMI formatted
    data. The first four lines are formatted as follows: "# [key]: [value]", with
    keys being title, artist, metre and tonic. These usually appear in this order,
    but not always!

    The "full.lab" file contains the chord annotation. Each line is tab seperated
    with chord start time, end time and name. Names follow a MIREX standard,
    which will be described when I know what it includes.
    """
    mcgill_song_directories = os.listdir(billboard_home)
    billboard_songs = dict()
    for song_dir in mcgill_song_directories:
        #read title, artist and starting tonic
        with open(os.path.join(billboard_home,song_dir,"salami_chords.txt"))\
            as salami_file:
            song_data = dict()
            line = salami_file.readline()
            while line != "\n":
                key, value = line.split(":",1) # titles can contain a ':'
                song_data[key[2:]] = value.strip()
                line = salami_file.readline()
            if len(song_data) != 4:
                print song_data
                
        #read song chords   
        with open(os.path.join(billboard_home,song_dir,"full.lab")) as lab_file:
            chords = []
            for line in lab_file.readlines():
                if line != "\n":
                    chords.append(line.split()[2])
        billboard_songs[(song_data['title'],song_data['artist'])] = \
            [song_data['tonic'], chords]

    chord_alphabet = set()
    tonic_alphabet = set()

    for tonic, chords in billboard_songs.values():
        tonic_alphabet.add(tonic)
        for chord in chords:
            chord_alphabet.add(chord)
    print "number of chord symbols:{}".format(len(chord_alphabet))
    return billboard_songs    
