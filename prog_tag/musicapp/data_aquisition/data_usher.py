import sys
import os
from chords.fetch_song import *
from musicapp.models import *
from django.core.exceptions import ObjectDoesNotExist
import random
import time
import pickle

def acquire_db_song_chords():
    """ 
    Acquires chords for songs in the db who don't have any yet.
    """
    number_of_songs_read = 0
    number_of_songs_failed = 0
    unchorded_songs = Song.objects.filter(chords__isnull=True, previously_failed_chords=False)
    print "number of songs without chords (that have not been queried yet) - ", len(unchorded_songs)
    chorded_songs = {(song.title, song.artist) for song in \
        Song.objects.filter(chords__isnull=False).distinct()}
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
            if not (number_of_songs_read % 30): print "saved chords for", \
                number_of_songs_read, "songs."
        except (ChordsNotFoundException, DecodingFailedException, Exception) as e: #later we might handle exceptions personally
            song.previously_failed_chords = True #later on we can find bad behaving songs
            song.save()
            #remove all chords that did get linked to the failed song
            for song_chord_index in Song_chord_index.objects.filter(song=song): song_chord_index.delete()
            number_of_songs_failed += 1
            if not (number_of_songs_failed % 300): print "failed saving chords for", \
                number_of_songs_failed, "songs."
        #restart program after two hours, since we get weird results otherwise
        if time.time() - start >= 2*60*60:
            python = sys.executable
            os.execl(python, python, * sys.argv)
                  
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
        chord, is_new = Chord.objects.get_or_create(root=root, notes=str(notes), symbol = chord)            
#            if is_new: print "created new chord instance - ", root, notes              
        #create the chord_index relationship
        Song_chord_index.objects.create(song=song, chord=chord, index=index)   
    song.previously_failed_chords = False #if this attempt succeeded, remove bad flag

def produce_partial_unchorded_song_lists(amount_of_files):
    unchorded_songs = Song.objects.filter(chords__isnull = True, ).distinct()
    song_num = len(unchorded_songs)
    path = "C:/Users/arielbro/Documents/chord_progression_project/song_list"
    for file_number in range(amount_of_files):
        with open(path + str(file_number),'w') as output_file:
    #        pickle.dump({(song.title, song.artist) for song in unchorded_songs[file_number*(song_num//amount_of_files):\
    #                                                                           (file_number+1)*(song_num//amount_of_files)]},\
    #                                                                           output_file)
            for song in unchorded_songs[file_number*(song_num//amount_of_files):(file_number+1)*(song_num//amount_of_files)]:
                try:
                    output_file.write(song.title + "\t" + song.artist + "\n")
                except:
                    continue

def incorporate_song_chords_from_external_source(source_path):
    """ 
    Given the path of a file containing chords for songs, fill up the database with objects built upon this data.
    Assumes file is a pickle of a dictionary containing (title, artist) pairs as keys, and iterables of textual chords as values.
    """
    number_of_songs_read = 0
    number_of_songs_with_existing_chords = 0
    songs_to_chords = pickle.load(open(source_path,'r'))
    start_time = time.time()
    #'\r' endings result from windows and linux handling line breaks differently (external source from linux mahcine)
    songs_to_chords = {(key[0],key[1].replace('\r','')):value for key,value in songs_to_chords.items()}
    print len(songs_to_chords), "songs to update with chords from file", source_path.split("/")[-1]
    for title,artist in songs_to_chords.keys():
        try:
            song = Song.objects.get(title=title, artist=artist, chords__isnull=True)    
            chord_vector = songs_to_chords[title,artist]
            for index,chord in enumerate(chord_vector):
                root, notes = decode(chord)
                    
                chord, is_new = Chord.objects.get_or_create(root=root, notes=str(notes), symbol = chord)            
                Song_chord_index.objects.create(song=song, chord=chord, index=index)   
    
            number_of_songs_read += 1
            if not (number_of_songs_read % 100): print "saved chords for", \
                number_of_songs_read, "songs."
        except ObjectDoesNotExist:
#            print title.__repr__(),artist.__repr__()
#            song = Song.objects.get(title=title, artist=artist)#make sure song does appear, but with chords
            number_of_songs_with_existing_chords += 1
            continue
        except DecodingFailedException as e:
            #remove all chords that did get linked to the failed song
            for song_chord_index in Song_chord_index.objects.filter(song=song): song_chord_index.delete()
            print e
            continue
        except Exception as e:#assume exception was before chord decoding phase.
            print e
            continue
    print "done updating", len(songs_to_chords), ',', number_of_songs_with_existing_chords, \
        " of them already updated. Time taken", ((time.time() - start_time)//6)/10, "minutes"

#produce_partial_unchorded_song_lists(8)
#acquire_db_song_chords()

#print len(Song_chord_index.objects.all())
#for song_chord_index in Song_chord_index.objects.all(): song_chord_index.delete()
#print 'done cleaning song-chord links'
#for chord in Chord.objects.all(): chord.delete()
#print 'done removing all chords'
#for song in Song.objects.filter(previously_failed_chords=True): 
#    song.previously_failed_chords = False
#    song.save()
#print 'done resetting chord-fail statuses'

external_chords_path = 'C:/Users/arielbro/Documents/chord_progression_project'
for file_name in os.listdir(external_chords_path):
    if 'output_dict' in file_name:
        incorporate_song_chords_from_external_source(external_chords_path + '/' + file_name)    
