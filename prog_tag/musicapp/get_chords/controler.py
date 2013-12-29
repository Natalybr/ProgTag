
import get_chords_midi as midi
import get_chords_sites as sites

"""
TODO: somehow sync all results to filter noise, 
and return the "clean" chord vector
"""
def get_chords(title,artist):
    
    chord_vector_m = midi.get_chords(title, artist)
    chord_vector_s = sites.get_chords(title, artist)


    
    
    