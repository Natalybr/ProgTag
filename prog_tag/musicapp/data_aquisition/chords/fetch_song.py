
import sources.ultimate_guitar as sites_ug
import sources.e_chords as sites_ec
import sources.chordie as sites_ch

class ChordsNotFoundException(Exception):
    title,artist = None, None
    def __init__(self, title, artist):
        self.title, self.artist = title, artist
    def __str__(self):
        return "Could not find chords for song - " + self.title + ", by - " + self.artist

"""
Testing funtion -
it gets all chord vectors from all sources and prints them
"""
def get_chords(title,artist):
#    print "Starting..."
    chord_vector_s = sites_ec.get_chords(title, artist)
#    print "e-chords: "+str(chord_vector_s)
    chord_vector_u = sites_ug.get_chords(title, artist)
#    print "ultimate: "+str(chord_vector_u)
    chord_vector_c = sites_ch.get_chords(title, artist)
#    for chord_vector_c in chord_vectors_c:
#        print "chordie: "+str(chord_vector_c)
#    print "That's it!"
    
    # TODO choose between vectors (in the right way)
    if chord_vector_s:
        return chord_vector_s
    if chord_vector_u:
        return chord_vector_u
    if chord_vector_c:
        return chord_vector_c
    raise ChordsNotFoundException(title,artist)
    
    

def test():
    get_chords("One to all","Yakuzi") 