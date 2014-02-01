from chords.fetch_song import *
from musicapp.models import *
from django.core.exceptions import ObjectDoesNotExist
import random
import time

def acquire_db_song_chords():
    """ 
    Acquires chords for songs in the db who don't have any yet.
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
    rand = random.Random()
    rand.seed()
    rand.shuffle(list(unchorded_songs))
    print 'starting iterations'
    for song in unchorded_songs:
        if song.previously_failed_chords: continue #currently try only fresh things
        start = time.time()
        try:
            acquire_song_chords(song.title,song.artist)
            number_of_songs_read += 1
            print 'successful song took ' + str(time.time() - start) + ' seconds'
            if not (number_of_songs_read % 100): print "saved chords for", \
                number_of_songs_read, "songs."
        except (ChordsNotFoundException, DecodingFailedException, Exception) as e: #later we might handle exceptions personally
            song.previously_failed_chords = True #later on we can find bad behaving songs
            song.save()
            number_of_songs_failed += 1
#            print e
#            print 'failed song took ' + str(time.time() - start) + ' seconds'
            if not (number_of_songs_failed % 100): print "failed saving chords for", \
                number_of_songs_failed, "songs."
                  
def acquire_song_chords(title, artist):
    """
    Acquires chords for one song, assuming it exists in database and has no chords saved yet.
    """
    #search for song in database, and demand that it has no chords (otherwise an exception is thrown by db)
    song = Song.objects.get(title=title, artist=artist, chords__isnull=True)    
    chord_vector = get_chords(song.title, song.artist)
    for index,chord in enumerate(chord_vector):
        root, notes = decode(chord)
        #instead of creating a huge amount of duplicated Chord instances, 
        #create a new instance only for a first appearing chord in the db.
        chord, is_new = Chord.objects.get_or_create(root=root, notes=str(notes))            
#            if is_new: print "created new chord instance - ", root, notes              
        #create the chord_index relationship
        Song_chord_index.objects.create(song=song, chord=chord, index=index)   
    song.previously_failed_chords = False #if this attempt succeeded, remove bad flag

acquire_db_song_chords()