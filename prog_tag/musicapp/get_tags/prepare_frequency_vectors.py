# -*- coding: utf-8 -*-
from get_intersected_songs_data import get_intersected_songs_data
import csv
min_progression_len = 3
max_progression_len = 15
progression_occurence_threshold = 0.01
# maybe relative to the size of the data?
# or better yet, relative also to progression_len (done!)

def compute_modulus(chord, tonic):
    """
    Computes the modulus of a chord by a tonic.
    Assumes chords are formatted
    as [key]:[modus], with key belonging to {A,B,...,G}X{#,b}union{N}, with
    N or X standing for no chord.
    Return the chord with [modulus]:[modus], with modus untuched, and modulus
    between 0 and 11
    """
    key_values = {'A':0,'B':2,'C':3,'D':5,'E':7,'F':8,'G':10}
    translation_values = {'#':1,'b':-1,'♮':0}
    #parse chord
    if not ':' in chord:
        if(not chord in {'X','N'}):
            raise Exception("unreconized chord:" + chord)
        return 'N'
    key,modus = chord.split(':')
    if len(key)>=2:
        translation = key[1]
        key = key[0]
    else:
        translation = '♮'
    if (not key in key_values) or (not translation in translation_values):
        raise Exception("unrecognized chord:" + chord)
    #parse tonic
    if len(tonic)>=2:
        tonic_translation = tonic[1]
        tonic_key = tonic[0]
    else:
        if tonic in {'X','N'}:
            print 'warning - no tonic'
            return 'N'
        if not tonic in key_values:
            raise Exception("unrecognized tonic:" + tonic)
        tonic_translation = '♮'
        tonic_key = tonic
    return str((key_values[key] + translation_values[translation] - \
                key_values[tonic_key] - translation_values[tonic_translation])%\
               12) + ":" + modus

def appears_with_overlap(progression_len, song, index):
    """
    For a progression of length progression_len, returns true iff exists
    i<k such that
    song[index:index+progression_len]=song[index+i:index+i+progression_len],
    i.e. the progression found at that index overlaps itself.
    """
    for translation in range(progression_len):
        if song[index:index+progression_len] == \
           song[index+translation:index+translation+progression_len]:
            return True
    return False
        
        
    

"""
Create a song:(progression_frequency_vector,tags_ dictionary from chords and
tags data.

1. Translate (tonic,chords) data to (chords modulus tonic) data
1. Go over the chords data with increasing window sizes to find all harmonic
progression of length below a threshold. Keep count of who appears and how much.
2. Define coordinates in frequency vector - all progressions that appear
above a threshold. The order is irrelevant, as long as consistent.
3. Go over the chords data again, and convert each chords vector to frequency
vector.
4. Output format - ?

"""

song_chords, song_tags = get_intersected_songs_data()

#translate (tonic,chords) data to modulus data
for song in song_chords.keys():
    tonic = song_chords[song][0]
    song_modulus_chords = [compute_modulus(chord, tonic) for chord in\
                           song_chords[song][1]]
    #important! currently we remove consecutive duplicate chords!
    song_modulus_chords = [chord for index,chord in \
        enumerate(song_modulus_chords) if index == len(song_modulus_chords)-1 or
        song_modulus_chords[index+1] != chord]
    song_chords[song] = song_modulus_chords
     
     

#compute harmonic progressions
progression_average_frequency = dict()
for song in song_chords.keys():
    chords = tuple(song_chords[song])
    for progression_len in range(min_progression_len, max_progression_len):
        for start_index in range(len(chords) - progression_len + 1):
            progression = chords[start_index:start_index + progression_len]
            if not appears_with_overlap(progression_len, chords, start_index):
                progression_average_frequency[progression] = \
                    progression_average_frequency.get(progression,0) + \
                    float(progression_len)/len(song_chords.keys())

#Define the progressions coordinate system
index = 0
progressions = (progression for progression,occurences in \
                      progression_average_frequency.items() if occurences >= \
                      progression_occurence_threshold)
#Store frequency coordinate system in a dict, for easy index finding
progression_indices = {progression : index for index,progression in \
                      enumerate(progressions)}

frequency_len = len(progression_indices)
print "length of frequency vectors={}".format(frequency_len)

#Compute frequency vectors
frequency_vectors = dict()
for song in song_chords.keys():
    chords = tuple(song_chords[song])
    frequency_vector = [0]*frequency_len
    for progression_len in range(min_progression_len, max_progression_len):
        for start_index in range(len(chords) - progression_len + 1):
            progression = chords[start_index:start_index + progression_len]
            if progression in progression_indices and \
               not appears_with_overlap(progression_len, chords, start_index):
                frequency_vector[progression_indices[progression]] += \
                    float(progression_len)/len(chords)
    frequency_vectors[song] = tuple(frequency_vector)
                         
#Define the tagging coordinate system
tags = reduce(lambda x,y: x.union(y), (tags for tags in\
                                       song_tags.values()))
#filter low occurencing tags
#tags_average_appearances = 
print 'number of selected tags={}'.format(len(tags))
#define an arbitrary order, and store the indexing in a dict
tag_indices = {tag : index for index, tag in enumerate(tags)}

#compute tagging vectors
tagging_vectors = dict()
tag_len = len(tags)
for song in song_tags.keys():
    tag_vector = [0]*tag_len
    for tag in song_tags[song]:
        tag_vector[tag_indices[tag]] = 1 #binary values
    tagging_vectors[song] = tuple(tag_vector)

#output a CSV with (frequency vectors, tags) fixed length lines, by defining
#an order on the tags. First line consists of headers
with open('../Data/Intermediate/frequency_vectors.csv','wb') as out_file:
    writer = csv.writer(out_file)
    #write headers
    headers = ['']*(frequency_len + tag_len + 2)#+2 for title and artist
    inverse_tag_indices = {index:tag for tag,index in tag_indices.items()}
    inverse_progression_indices = {index:progression for progression,index\
                                   in progression_indices.items()}
    headers[0] = 'title'
    headers[1] = 'artist'
    for i in range(frequency_len):
        headers[i + 2] = inverse_progression_indices[i]
    for i in range(tag_len):
        headers[frequency_len + i + 2] = inverse_tag_indices[i]
    writer.writerow(headers)
    #write data
    for song in frequency_vectors.keys():
        writer.writerow(song + frequency_vectors[song] + tagging_vectors[song]) 
    print 'done writing {} songs data'.format(len(frequency_vectors.keys()))
