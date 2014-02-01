# -*- coding: utf-8 -*-
import csv
from musicapp.models import * 
min_progression_len = 3
max_progression_len = 15
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
    for song in Song.objects.filter(chords__isnull=False, progressions__isnull=True):
        create_song_progressions(song, min_progression_len, max_progression_len)
    
def create_song_progressions(song, min_size, max_size):
    """
    Create a dict of all (non-overlapping) chord progressions from a song,
    mapped to each one's number of appearances.
    What is considered 'chord' in the progressions is different than the Chord class in the 
    db - here we only consider the relative differences and (modulus) notes, not the 
    root key or the original representing symbol.
    """
    
    #fetch all the chords a song has as an ordered tuple
#    for pair in Song_chord_index.objects.all():
#        print pair
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
                    notes=chords[i].notes)[0] if i else \
                   Abstract_chord.objects.get_or_create(\
                    root_difference=0, notes = chords[0].notes)[0]\
                   for i in range(chord_number)]#each progression starts with relative difference 0
     
    #go over different progressions
    for size in range(min_size, max_size + 1): 
        for start_index in range(chord_number - (size-1)):
            progression_chords = differences[start_index:start_index+size]
            #check if this progression exists
            potential_progressions = Chord_progression.objects.filter(length=size)
#            print "initial candidates: " + str(len(potential_progressions))
#            for candidate in potential_progressions:
#                print Progression_chord_index.objects.get(progression=candidate, index=0)
            for match_index in range(size):
                #check if i'th chord is this chord by filter chaining                 
                if not potential_progressions: continue
                
                #(http://stackoverflow.com/questions/5489618/django-filter-through-multiple-fields-in-a-many-to-many-intermediary-table)
                if not match_index:
                    potential_progressions = potential_progressions.filter(\
                        progression_chord_index__index=match_index, \
                        progression_chord_index__chord=normalized_differences[start_index + match_index])
                else:
                    potential_progressions = potential_progressions.filter(\
                        progression_chord_index__index=match_index, \
                        progression_chord_index__chord=progression_chords[match_index])
#                print 'got down to:', len(potential_progressions)
            assert len(potential_progressions) <= 1
            if len(potential_progressions) == 1: #progression already exists
                progression = potential_progressions[0]
                progression.appearances += 1 #currently there is no normalizing by song length!
                song_link = Song_progression_count.objects.get_or_create(song=song, progression=progression)[0]
                song_link.appearance_count += 1
            else:
                progression = Chord_progression.objects.create(appearances=1, length=size)
                for index in range(size):
                    if not index:
                        Progression_chord_index.objects.create(progression=progression, \
                                                               chord=normalized_differences[start_index + match_index], \
                                                               index=index)
                    else:
                        Progression_chord_index.objects.create(progression=progression, chord=progression_chords[index], \
                                                               index=index)
                song_link = Song_progression_count.objects.create(song=song, progression=progression)
                song_link.appearance_count = 1
            progression.save()
            song_link.save()
            
        
