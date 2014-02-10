# -*- coding: utf-8 -*-
import csv
from musicapp.models import *
import time
import random
progression_lengths = [4]
progression_occurence_threshold = 0.005
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
    print "number of songs with chords and no progressions- " + \
        str(len(Song.objects.filter(chords__isnull=False, progressions__isnull=True).distinct()))
    print "number of songs with progressions- " + str(len(Song.objects.filter(progressions__isnull=False).distinct()))
    songs_to_cover = list(Song.objects.filter(chords__isnull=False, progressions__isnull=True))
    random.shuffle(songs_to_cover)
    print 'starting iterations'
    for song in songs_to_cover:
        create_song_progressions(song, progression_lengths)
        progress += 1
        if not progress % 10:
            print "created progressions for", progress, "songs. Time taken:", ((time.time() - start_time)//6)/10, "minutes"
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

def create_db_progressions_buffered():
    progress = 0
    start_time = time.time()
    print "number of songs with chords and no progressions- " + \
        str(len(Song.objects.filter(chords__isnull=False, progressions__isnull=True).distinct()))
    print "number of songs with progressions- " + str(len(Song.objects.filter(progressions__isnull=False).distinct()))
    songs_to_cover = list(Song.objects.filter(chords__isnull=False, progressions__isnull=True))
    random.shuffle(songs_to_cover)
    bulk_size = 2000
    print 'starting iterations (bulk size', bulk_size, ")"
    for i in range(len(songs_to_cover)//bulk_size + 1):
        try:
            create_song_progressions_buffered(songs_to_cover[i*bulk_size:(i+1)*bulk_size], progression_lengths)
            progress += bulk_size
            print "created progressions for", progress, "songs. Time taken:", ((time.time() - start_time)//6)/10, "minutes"
        except Exception as e:
            print "failed creating bulk of progressions. Time wasted:",((time.time() - start_time)//6)/10, "minutes"
            print e
        start_time = time.time()        

def create_song_progressions_buffered(songs, desired_lengths):
    """A buffered version of create_chord_progressions. This utilizes the assumed property of songs having lots of recurring
    progressions. database is only accessed at the end of the function run, preferring local representations comparisons."""
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
    print 'Done processing buffered data in',((time.time()-start_time)//6)/10,'minutes. Starting db communication.'
    print 'progressions', len(progressions_information)
    print 'chords', len(abstract_chords)
    print 'number of song_progression links', sum(sum(appearance_dict.values())\
                                                   for appearance_dict in progressions_information.values())
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
                db_progression = Chord_progression.objects.create(appearances=0, length=len(progression))
                try:
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
                song_link.save
            db_progression.appearances += sum(progressions_information[progression].values())
            db_progression.save()
        except Exception as e:
            print "cleaning up progression after song linking fail. Error-", e
            db_progression.delete() #cleans all foreign_key links, i.e. progression-chord-indices and progression-song-links.
            continue
        successful_progressions += 1
        if not successful_progressions % 100: 
            print 'progressions registered:', successful_progressions
            print 'ETA:', (((time.time()-start_time)*(len(progressions_information)/successful_progressions) - 1)//6)/10,\
                 'minutes.'
            
            

            
for song_link in Song_progression_count.objects.all():
    song_link.delete()
for progression in Chord_progression.objects.all():
    progression.delete()
for abstract_chord in Abstract_chord.objects.all():
    abstract_chord.delete()
    
#create_db_progressions()    
create_db_progressions_buffered()