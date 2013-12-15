from read_billboard_chords import read_billboard_songs
#from read_last_fm_tags import read_last_fm_tags
from read_last_fm_tags import last_fm_tags_iterator
import os
import pickle
intersection_cache_path = "../Data/Intermediate/intersection"

"""
Intersect song chords data and song tags data, as returned by the corresponding
modules, and return two dictionaries with structure
(title,artist):(starting_tonic,chord_list),
(title,artist):(tag_set),
respectively.

Cache the results, so further calls do not require recomputation
(currently there is no check made to ensure the cache is built from the same
data as we plan on using!!!)
"""
def get_intersected_songs_data():
    if os.path.isfile(intersection_cache_path):
        with open(intersection_cache_path, 'r') as cache:
            print "using cached version of intersected chords-tags data"
            return pickle.load(cache)
    else:
        print "computing intersection of chords-tags data"
        song_chords = read_billboard_songs()
        intersection_chords = dict()
        intersection_tags = dict()
        for song, tags in last_fm_tags_iterator():
            if song in song_chords:
                intersection_tags[song] = tags
                intersection_chords[song] = song_chords[song]
        """
        song_tags = read_last_fm_tags()
        intersection_keys = set(song_chords.keys()).intersection(\
            set(song_tags.keys()))
        intersection_chords = {key:song_chords[key] for\
                               key in intersection_keys}
        intersection_tags = {key:song_tags[key] for\
                              key in intersection_keys}
        """
        with open(intersection_cache_path, 'w') as cache:        
            pickle.dump((intersection_chords, intersection_tags),cache)
        print "Number of songs in intersection={}".format(len(intersection_tags))
        return intersection_chords, intersection_tags
