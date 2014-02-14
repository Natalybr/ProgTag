from musicapp.models import *
import pickle

path_to_chord_information = './chord_information'
path_to_progression_information = './progression_information'

def extract_chord_information_from_db():
    """
    To speed up performance during the ML experimental phase, extract all chord information from the db and store it in 
    a python dict, to be pickled and unpickled at need.
    """
    song_to_chords = dict()
    for song in Song.objects.all():
        chords = [None] * song.chords.count()
        for song_chord_index in Song_chord_index.objects.filter(song=song):
            chords[song_chord_index.index] = song_chord_index.chord
        for chord in chords: assert chord #remove later
        song_to_chords[(song.title,song.artist)] = chords
    pickle.dump(song_to_chords, open(path_to_chord_information,'w'))
        
def compute_chord_progressions_no_db():
    song_to_chords = pickle.load(open(path_to_chord_information,'r'))
    for song,chords in song_to_chords.items():
        differences = [((chords[i].root-chords[i-1].root)%12, chords[i].notes) if i else \
                       (0, chords[0].notes) for i in range(len(chords))]
        normalized_differences = [(0, chords[i].notes) for i in range(len(chords))]
        