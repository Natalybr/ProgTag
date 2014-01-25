from chords.fetch_song import *
from musicapp.models import *
from django.core.exceptions import ObjectDoesNotExist

def aquire_song_chords():
    """ 
    Aquires chords for songs in the db who don't have any yet.
    """
    number_of_songs_read = 0
    number_of_songs_failed = 0
    unchorded_songs = Song.objects.filter(chords__isnull=True)
    print "number of songs without chords - ", len(unchorded_songs)
    chorded_songs = {(song.title, song.artist) for song in \
        Song.objects.filter(chords__isnull=False)}#for a song with n chords there are  n entries
    print "number of songs with chords - ", len(chorded_songs)
#    for song in chorded_songs:
#        print song
    for song in unchorded_songs:
        #fetch chords from some site
        try:
            chord_vector = get_chords(song.title, song.artist)
        except (ChordsNotFoundException, Exception) as e:
#            if type(e)==ChordsNotFoundException: print e
#            else:
#                print "Encountered general exception during site chord fetching - (passing on)"
#                print e
                
            song.previously_failed_chords = True #later on we can find bad behaving songs
            song.save()
            number_of_songs_failed += 1
            if not (number_of_songs_failed % 100): print "failed saving chords for", \
                number_of_songs_failed, "songs."
            continue
        
        last_chord = None
        #convert to our Chord object format
        for index,chord in enumerate(chord_vector):
            root, notes = decode(chord)
            relative_difference = None if not last_chord else (root - last_chord.root)%12
            #instead of creating a huge amount of duplicated Chord instances, 
            #create a new instance only for a first appearing chord in the db.
            chord, is_new = Chord.objects.get_or_create(root=root, notes=str(notes), original=chord ,\
                                                        relative_difference=relative_difference)
            if is_new: print "created new chord instance - ", root, notes, relative_difference              
            #create the chord_index relationship
            Chord_index.objects.create(song=song, chord=chord, index=index)
        
        song.previously_failed_chords = False #if this attempt succeeded, remove bad flag
        number_of_songs_read += 1
        if not (number_of_songs_read % 100): print "saved chords for", \
            number_of_songs_read, "songs."
            
aquire_song_chords()