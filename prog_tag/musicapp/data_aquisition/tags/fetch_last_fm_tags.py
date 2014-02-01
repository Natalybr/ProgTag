import os
import json
from musicapp.models import *
from django.core import management

last_home = "C:/Users/arielbro/Documents/chord_progression_project/Data/last.fm/lastfm_train"
certainty_threshold = 85
def read_last_fm_tags():
    """
    read the last.fm s ong tags dataset, and return a dictionary, where the keys
    are (song_title,artist) tuples, and the values are tag sets.

    The dataset is formatted in nested subdirectories, where each file contains
    one json line, formatted as a dictionary, with "title","artist" and "tags"
    among them. the "tags" value contains a list of lists, each list contains
    the tag name, and certainty value (? last.fm didn't specify that), ranging
    from 0 to 100. We filter out the tags with a certainty threshold.
    """
    last_songs  = dict()
    average_tags_per_song = 0
    number_of_songs_with_tags = 0
    number_of_songs = 0
    #iterate over dataset files
    for root, dirs, files in os.walk(last_home):
        for song_file_path in files:
            number_of_songs += 1
            with open(os.path.join(root,song_file_path)) as song_file:
                song_data = json.loads(song_file.readline())
                #if song_data['tags']:
                certain_tags = {tag for tag,certainty in song_data['tags'] if \
                    int(certainty) >= certainty_threshold}
                if certain_tags: number_of_songs_with_tags+=1
                average_tags_per_song += len(certain_tags)
                last_songs[(song_data['title'],song_data['artist'])]=\
                    certain_tags
            if not number_of_songs % 20000:
                print "songs_read={}".format(number_of_songs)
    average_tags_per_song /= float(number_of_songs)
    print ("number of songs = {0}\nnumber of songs with tags = {1}\naverage number "\
        +" of tags per song = {2}").format(number_of_songs,number_of_songs_with_tags,\
                                       average_tags_per_song)
    return last_songs    

def last_fm_tags_iterator():
    """
    iterate over the last.fm song tags dataset, each time returning a
    ((song_title,artist),tag_set) pair. This will allow the user to filter
    only songs they need during fly time,
    instead of keeping whole of the dataset in memory.
    """
    
    last_songs  = dict()
    average_tags_per_song = 0
    number_of_songs_with_tags = 0
    number_of_songs = 0
    #iterate over dataset files
    for root, dirs, files in os.walk(last_home):
        for song_file_path in files:
            number_of_songs += 1
            with open(os.path.join(root,song_file_path)) as song_file:
                song_data = json.loads(song_file.readline())
                #if song_data['tags']:
                certain_tags = {tag for tag,certainty in song_data['tags'] if \
                    int(certainty) >= certainty_threshold}
                if certain_tags: number_of_songs_with_tags+=1
                average_tags_per_song += len(certain_tags)
                yield (song_data['title'],song_data['artist']),certain_tags
            if not number_of_songs % 5000:
                print "songs_read={}".format(number_of_songs)
    average_tags_per_song /= float(number_of_songs)
    print ("number of songs = {0}\nnumber of songs with tags = {1}\naverage number "\
        +" of tags per song = {2}").format(number_of_songs,number_of_songs_with_tags,\
                                       average_tags_per_song)    

def update_database_with_last_fm_tags():
    for (title, artist), tags in last_fm_tags_iterator():
        #chords go through Chord_index
        song, created = Song.objects.get_or_create(title=title, artist=artist)
        if not created: continue
        tags=[Tag.objects.get_or_create(name=tag) for tag in tags]
        (song.tags.add(tag) for tag in tags)
        #when fails, there's some rollback problem
        song.save()
    print 'done updating database'
    
management.call_command('syncdb', verbosity=0, interactive=False)
#management.call_command('flush', verbosity=0, interactive=False)
update_database_with_last_fm_tags()