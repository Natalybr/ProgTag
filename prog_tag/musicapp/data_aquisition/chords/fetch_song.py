
import sources.ultimate_guitar as sites_ug
import sources.e_chords as sites_ec
import sources.chordie as sites_ch
from time import sleep 
 
class ChordsNotFoundException(Exception):
    title,artist = None, None
    def __init__(self, title, artist):
        self.title, self.artist = title, artist
    def __str__(self):
        return "Could not find chords for song - " + self.title + ", by - " + self.artist

"""
try to get a chord vector from any of the sources.
when a vector is found - it's returned. 
if no source returns a vector - a 'ChordsNotFoundException' is raised.
"""
def get_chords(title,artist):
    
    sleep(3)
    
    chord_vectors_c = sites_ch.get_chords(title, artist)
    for chord_vector_c in chord_vectors_c:
        if chord_vector_c:
            return chord_vector_c
   
    chord_vector_ec = sites_ec.get_chords(title, artist)
    if chord_vector_ec:
        return chord_vector_ec
    
    chord_vector_u = sites_ug.get_chords(title, artist)
    if chord_vector_u:
        return chord_vector_u
    
    raise ChordsNotFoundException(title,artist)
    
    

def print_all_vectors(title, artist):
    print "Starting..."
    chord_vector_s = sites_ec.get_chords(title, artist)
    print "e-chords: "+str(chord_vector_s)
    chord_vector_u = sites_ug.get_chords(title, artist)
    print "ultimate: "+str(chord_vector_u)
    chord_vectors_c = sites_ch.get_chords(title, artist)
    for chord_vector_c in chord_vectors_c:
        print "chordie: "+str(chord_vector_c)
    print "That's it!"

def test():
    print_all_vectors("One to all","Yakuzi")
