# -*- coding: utf-8 -*-
import csv
from musicapp.models import *
import time
import math
import random
from musicapp.common_tasks import *
import sys

progression_lengths = [4]
# maybe relative to the size of the data?
# or better yet, relative also to progression_len (done!)

def appears_with_overlap(progression_len, chord_vector, index):
    """
    For a progression of length progression_len, returns true iff exists
    i<k such that
    chord_vector[index:index+progression_len]==chord_vector[index+i:index+i+progression_len],
    i.e. the progression found at that index overlaps itself.
    """
    for translation in range(progression_len):
        if chord_vector[index:index+progression_len] == \
           chord_vector[index+translation:index+translation+progression_len]:
            return True
    return False
        
def create_db_progressions():
    progress = 0
    start_time = time.time()
    songs_to_cover = list(Song.objects.filter(chords__isnull=False, progressions__isnull=True).distinct())
    print "number of songs with chords and no progressions- " + \
        str(len(songs_to_cover))
    print "number of songs with progressions- " + str(len(Song.objects.filter(progressions__isnull=False).distinct()))
    random.shuffle(songs_to_cover)
    print 'starting iterations'
    for song in songs_to_cover:
        create_song_progressions(song, progression_lengths)
        progress += 1
        if not progress % 10:
            print "created progressions for", progress, "songs. Time taken:", time_elapsed_minutes(start_time)
            start_time = time.time()            
                
def create_song_progressions(song, desired_lengths):
    """
    Create a dict of all (non-overlapping) chord progressions from a song,
    mapped to each one's number of appearances.
    What is considered 'chord' in the progressions is different than the Chord class in the 
    db - here we only consider the relative differences and (modulus) notes, not the 
    root key or the original representing symbol.
    """
    chord_index_pairs = [(pair.index, pair.chord) for pair in \
                         Song_chord_index.objects.filter(song=song)]
    chord_number = max((index+1 for index, chord in chord_index_pairs))
    chords = [None]*chord_number
    for index, chord in chord_index_pairs: chords[index] = chord
    #transform chord list to differences list with relative roots - first chord considered
    #with relative root 0. 
    differences = [Abstract_chord.objects.get_or_create(\
                    root_difference=(chords[i].root-chords[i-1].root)%12, 
                    notes=chords[i].notes)[0] if i else \
                   Abstract_chord.objects.get_or_create(\
                    root_difference=0, notes = chords[0].notes)[0]\
                   for i in range(chord_number)]
    normalized_differences = [Abstract_chord.objects.get_or_create(\
                    root_difference=0, 
                    notes=chords[i].notes)[0] for i in range(chord_number)]#each progression starts with relative difference 0
     
    #go over different progressions
    for size in desired_lengths: 
        for start_index in range(chord_number - (size-1)):
            progression_chords = differences[start_index:start_index+size]
            progression_chords[0] = normalized_differences[start_index]
            #check if this progression exists
            potential_progressions = Chord_progression.objects.filter(length=size).distinct()
            for match_index in range(size):
                #check if i'th chord is this chord by filter chaining                 
#                if not potential_progressions: continue #this forces hitting the db, which is costly and disables optimization.
                #(http://stackoverflow.com/questions/5489618/django-filter-through-multiple-fields-in-a-many-to-many-intermediary-table)
                potential_progressions = potential_progressions.filter(\
                    progression_chord_index__index=match_index, \
                    progression_chord_index__chord=progression_chords[match_index]).distinct()
            if len(potential_progressions) > 1:
                print "more than one potential progression to match progression - "
                for chord in progression_chords: print chord
                print "possible matches - " 
                for potential_progression in potential_progressions: print potential_progression 
                exit()
            if len(potential_progressions) == 1: #progression already exists
                progression = potential_progressions[0]
                progression.appearances += 1 #currently there is no normalizing by song length!
                song_link = Song_progression_count.objects.get_or_create(song=song, progression=progression)[0]
                song_link.appearance_count += 1
            else:
                progression = Chord_progression.objects.create(appearances=1, length=size)
                for index in range(size):
                    Progression_chord_index.objects.create(progression=progression, chord=progression_chords[index], index=index)
                song_link = Song_progression_count.objects.create(song=song, progression=progression)
                song_link.appearance_count = 1
            progression.save()
            song_link.save()

def create_db_progressions_buffered(buffer_size):
    progress = 0
    start_time = time.time()
    songs_to_cover = list(Song.objects.filter(chords__isnull=False, progressions__isnull=True, tags__isnull=False).distinct())
    print "number of songs with chords, tags and no progressions- " + \
        str(len(songs_to_cover))
    #filter to only songs with tags
    print "number of songs with progressions- " + str(len(Song.objects.filter(progressions__isnull=False).distinct()))
    random.shuffle(songs_to_cover)
    print 'starting iterations (buffer size', buffer_size, ")"
    for i in range(int(math.ceil(len(songs_to_cover)/float(buffer_size)))):
        try:
            create_song_progressions_buffered(songs_to_cover[i*buffer_size:(i+1)*buffer_size], progression_lengths)
            progress += buffer_size
            print "created progressions for", progress, "songs. Time taken:", time_elapsed_minutes(start_time)
        except Exception as e:
            print "failed creating bulk of progressions. Time wasted:",time_elapsed_minutes(start_time)
            print e
        start_time = time.time()        

def create_song_progressions_buffered(songs, desired_lengths):
    """A buffered version of create_chord_progressions. This utilizes the assumed property of songs having lots of recurring
    progressions. database is only accessed at the end of the function run, preferring local representations comparisons."""
    abstract_chords = set() #format - set of (root_difference, notes tuple)) tuples.
    progressions_information = dict() #format - mapping from tuple(several (root_difference,note tuple)) to 
    #(title,artist):appearances dict.
    songs_with_registered_progressions = {song for song in songs if song in\
                                           Song.objects.filter(progressions__isnull=False).distinct()}
    if songs_with_registered_progressions:
        print 'warning: song list passed to progression creation contains {} songs with existing progressions. Skipping them.'.\
            format(len(songs_with_registered_progressions))
        songs = {song for song in songs if not song in songs_with_registered_progressions}
    start_time = time.time()
    for song in songs:
        chord_index_pairs = [(pair.index, pair.chord) for pair in \
                             Song_chord_index.objects.filter(song=song)]
        chord_number = max((index+1 for index, chord in chord_index_pairs))
        chords = [None]*chord_number
        for index, chord in chord_index_pairs: chords[index] = chord
        
        differences = [((chords[i].root-chords[i-1].root)%12, chords[i].notes) if i else \
                       (0, chords[0].notes) for i in range(chord_number)]
        normalized_differences = [(0, chords[i].notes) for i in range(chord_number)]

        #add record of abstract chords created for progressions in this song        
        for difference in differences: abstract_chords.add(difference)
        for normalized_difference in normalized_differences: abstract_chords.add(normalized_difference)
         
        #go over different progressions
        for size in desired_lengths: 
            for start_index in range(chord_number - (size-1)):
                progression_chords = differences[start_index:start_index+size]
                progression_chords[0] = normalized_differences[start_index]
                progression_chords = tuple(progression_chords)
                #check if this progression exists
                if not progression_chords in progressions_information:
                    progressions_information[progression_chords] = dict()
                    
                progressions_information[progression_chords][(song.title,song.artist)]=\
                    progressions_information[progression_chords].get((song.title,song.artist), 0) + 1
        
    """start feeding the database with the information gathered"""
    print 'Done processing buffered data in',time_elapsed_minutes(start_time), 'Starting db communication.'
    print 'progressions', len(progressions_information)
    print 'chords', len(abstract_chords)
    print 'number of song_progression links', sum(len(value) for value in progressions_information.values())
    #create abstract chords    
    abstract_chords_mapping = {(root_difference,notes):\
                               Abstract_chord.objects.get_or_create(root_difference=root_difference, notes=notes)[0] for \
                               (root_difference,notes) in abstract_chords}
    #create progressions
    start_time = time.time()
    successful_progressions = 0
    for progression in progressions_information.keys():
        potential_progressions = Chord_progression.objects.filter(length=len(progression)).distinct()
        for match_index in range(len(progression)):
            potential_progressions = potential_progressions.filter(\
                progression_chord_index__index=match_index, \
                    progression_chord_index__chord=\
                    abstract_chords_mapping[progression[match_index]]).distinct()
        if len(potential_progressions) > 1:
            print "more than one potential progression to match progression - "
            for chord in progression: print chord
            print "possible matches - " 
            for potential_progression in potential_progressions: print potential_progression 
            exit()
        if len(potential_progressions) == 0:
                try:
                    db_progression = Chord_progression.objects.create(appearances=0, length=len(progression))
                    for index in range(len(progression)):
                        Progression_chord_index.objects.create(progression=db_progression, \
                                                               chord=abstract_chords_mapping[progression[index]], index=index)
                except Exception as e:#clean up on any error.
                    print "cleaning up after progression creation fail. Error-", e
                    db_progression.delete() #cleans all foreign_key links to it as well, so all progression_chord_indices.
                    continue
        else:
            db_progression = potential_progressions[0]
        try:
            for title,artist in progressions_information[progression].keys():
                song_link = Song_progression_count.objects.get_or_create(\
                    song=Song.objects.get(title=title,artist=artist), progression=db_progression)[0]
                song_link.appearance_count += progressions_information[progression][(title,artist)]
                song_link.save()
            db_progression.appearances += sum(progressions_information[progression].values())
            db_progression.save()
        except Exception as e:
            print "cleaning up progression after song linking fail. Error-", e
            db_progression.delete() #cleans all foreign_key links, i.e. progression-chord-indices and progression-song-links.
            continue
        successful_progressions += 1
        if not successful_progressions % 100: 
            print 'progressions registered:', successful_progressions
            print 'ETA:', ((time.time()-start_time)*(len(progressions_information)/successful_progressions - 1)//6)/10,\
                 'minutes.'
            
def create_db_progressions_bulk(desired_lengths):
    """A bulk version of create_chord_progressions. This utilizes the assumed property of songs having lots of recurring
    progressions. database is only accessed at the end of the function run, preferring local representations comparisons.
    In addition, the db is accessed efficiently, with bulk_create, resulting in much-much less queries."""
    
    """IMPORTANT ASSUMPTION: db does not contain any progression"""
    assert Chord_progression.objects.all().count() == 0
    assert Song.objects.filter(progressions__isnull=False).count() == 0
    songs = Song.objects.filter(chords__isnull=False).distinct()
    abstract_chords = set() #format - set of (root_difference, notes tuple)) tuples.
    progressions_information = dict() #format - mapping from tuple(several (root_difference,note tuple)) to 
    #(title,artist):appearances dict.
    start_time = time.time()
    for song in songs:
        chord_index_pairs = [(pair.index, pair.chord) for pair in \
                             Song_chord_index.objects.filter(song=song)]
        chord_number = max((index+1 for index, chord in chord_index_pairs))
        chords = [None]*chord_number
        for index, chord in chord_index_pairs: chords[index] = chord
        
        differences = [((chords[i].root-chords[i-1].root)%12, chords[i].notes) if i else \
                       (0, chords[0].notes) for i in range(chord_number)]
        normalized_differences = [(0, chords[i].notes) for i in range(chord_number)]

        #add record of abstract chords created for progressions in this song        
        for difference in differences: abstract_chords.add(difference)
        for normalized_difference in normalized_differences: abstract_chords.add(normalized_difference)
         
        #go over different progressions
        for size in desired_lengths: 
            for start_index in range(chord_number - (size-1)):
                progression_chords = differences[start_index:start_index+size]
                progression_chords[0] = normalized_differences[start_index]
                progression_chords = tuple(progression_chords)
                #check if this progression exists
                if not progression_chords in progressions_information:
                    progressions_information[progression_chords] = dict()
                    
                progressions_information[progression_chords][(song.title,song.artist)]=\
                    progressions_information[progression_chords].get((song.title,song.artist), 0) + 1
        
    """start feeding the database with the information gathered"""
    print 'Done processing buffered data in',time_elapsed_minutes(start_time), 'Starting db communication.'
    print 'progressions', len(progressions_information)
    print 'chords', len(abstract_chords)
    print 'number of song_progression links', sum(len(value) for value in progressions_information.values())
    sys.stdout.flush()
    #create abstract chords    
    abstract_chords_mapping = {(root_difference,notes):\
                               Abstract_chord.objects.get_or_create(root_difference=root_difference, notes=notes)[0] for \
                               (root_difference,notes) in abstract_chords}
    #create progressions
    start_time = time.time()
    """"
    unfortunately, as mentioned in http://stackoverflow.com/questions/10799267/selecting-querying-objects-from-django-bulk-create
    the objects that were used for the bulk_create ARE NOT the ones created, and cannot be used for further queries/linking.
    Since querying back the created progressions is super-expensive (filtering based on chords one by one), and updating the
    models so that progressions hold a uniquly identifying field is complicated (unless willing to loose all data in db),
    the solution found was to rely on the fact that the primary key of created progressions is successively incremented.
    """
    progressions_to_create_dict = {chords:\
                                   (id+1, Chord_progression(length=len(chords),appearances=sum(appearances_dict.values())))\
                                   for id,(chords,appearances_dict) in enumerate(progressions_information.items())}#django id >= 1
    Chord_progression.objects.bulk_create(progression for id,progression in progressions_to_create_dict.values())

    print 'done creating progressions in', time_elapsed_minutes(start_time)
    start_time = time.time()
    progress = 0
    #create progression to chord and song to progression links.
    progression_chord_links_to_create = []#don't use sets, because django objects don't implement .__hash__ correctly for objects
    song_progression_counts_to_create = []#with inexisting pk
    progression_start_time = time.time()
    for chords,appearances_dict in progressions_information.items():
        progression = Chord_progression.objects.get(id=progressions_to_create_dict[chords][0])
        for index, chord_info in enumerate(chords):
            progression_chord_links_to_create.append(Progression_chord_index(progression=progression,\
                                                                          chord=abstract_chords_mapping[chord_info],index=index))
        for song in songs:
            if (song.title, song.artist) in appearances_dict:
                song_progression_counts_to_create.append(Song_progression_count(song=song,progression=progression,\
                                                                             appearance_count=appearances_dict[\
                                                                                            song.title,song.artist]))
        progress += 1
        if not progress % 10000:
            print 'done processing links for', progress, 'progressions in', time_elapsed_minutes(progression_start_time)
            progression_start_time = time.time()
    Progression_chord_index.objects.bulk_create(progression_chord_links_to_create)    
    Song_progression_count.objects.bulk_create(song_progression_counts_to_create)
    print 'done creating links in', time_elapsed_minutes(start_time)

print 'number of song links to delete:', Song_progression_count.objects.count()     
print 'number of progression chord links to delete:', Progression_chord_index.objects.count()       
print 'number of progressions to delete:', Chord_progression.objects.count()            
print 'number of abstract chords to delete:', Abstract_chord.objects.count() 
#can't delete instantly more than 999 items with foreignkey pointing at them :/
Song_progression_count.objects.all().delete() 
Progression_chord_index.objects.all().delete()
Abstract_chord.objects.all().delete()
delete_queryset(Chord_progression.objects.all())
    
#create_db_progressions()
#create_db_progressions_buffered(buffer_size=len(Song.objects.filter(chords__isnull=False,progressions__isnull=True).distinct()))
create_db_progressions_bulk([3,4,5,6])