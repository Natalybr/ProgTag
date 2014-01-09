
import sources.ultimate_guitar as sites_ug
import sources.e_chords as sites_ec
import sources.chordie as sites_ch

"""
Testing funtion -
it gets all chord vectors from all sources and prints them
"""
def get_chords(title,artist):
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
    get_chords("One to all","Yakuzi") 

test() 