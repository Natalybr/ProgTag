from musicapp.models import *
from musicapp.data_aquisition.chords.fetch_song import *
import numpy as np
from django.db import transaction

def similarity(first_song, second_song):
    """
    Computes the similarity between two songs, a number in the interval [0,1]. 
    The similarity is defined to be the amount of progressions (counting multiple appearances) shared by the two songs,
    divided by the half the total amount of progressions for both of them (i.e. their average progression number).
    
    Note - extremely unscalable.
    """
    first_song_progression_links = Song_progression_count.objects.filter(song=first_song).distinct()#distinct as a safety measure
    second_song_progression_links = Song_progression_count.objects.filter(song=second_song).distinct()
    first_progression_counts = {song_progression_link.progression:song_progression_link.appearance_count \
                                for song_progression_link in first_song_progression_links}
    second_progression_counts = {song_progression_link.progression:song_progression_link.appearance_count \
                                 for song_progression_link in second_song_progression_links}
    denominator = float(sum(count for count in first_progression_counts.values()) + \
                  sum(count for count in second_progression_counts.values()))/2
    nominator = sum(min(first_progression_counts[progression],second_progression_counts[progression]) \
                    for progression in set(first_progression_counts.keys()).intersection(second_progression_counts.keys()))
    return nominator/denominator

def compute_similarity_matrix_bulk(songs):
    song_progression_links = Song_progression_count.objects.filter(song__in=songs)
    progression_counts = {(song_progression_link.song,song_progression_link.progression):\
                            song_progression_link.appearance_count\
                            for song_progression_link in song_progression_links}
    #I should compute the progression count first for all songs individually
    similarity_matrix=np.zeros((len(songs),len(songs)))
    for i in range(len(songs)):
        similarity_matrix[i,i] = 1.0
    for i in range(len(songs)):
        for j in range(i+1, len(songs)):
            first_progression_counts = {progression:appearance_count for (song,progression),appearance_count\
                                         in progression_counts.items() if song==songs[i]}
            second_progression_counts = {progression:appearance_count for (song,progression),appearance_count\
                                         in progression_counts.items() if song==songs[j]}
            denominator = float(sum(count for count in first_progression_counts.values()) + \
                  sum(count for count in second_progression_counts.values()))/2
            if denominator ==0: 
                print len(first_progression_counts), float(sum(count for count in first_progression_counts.values()))
                print songs[i]
#                for progression in songs[i].progressions.all(): print progression
                print len(Song_progression_count.objects.filter(song=songs[i]))
                for count in Song_progression_count.objects.filter(song=songs[i]): print count.appearance_count
#                print 'second'
#                for progression in songs[j].progressions.all(): print progression
            nominator = sum(min(first_progression_counts[progression],second_progression_counts[progression]) \
                    for progression in set(first_progression_counts.keys()).intersection(second_progression_counts.keys()))
#            print 'nominator=',nominator
#            print 'denominator=',denominator
            similarity_matrix[i,j]=similarity_matrix[j,i]=nominator/denominator
    return similarity_matrix

def compute_average_similarity_between_adjacent_pairs(songs):
    """
    Given an iterable of songs, computes the average similarity between pairs song[i],song[i+1].
    For some fear of probability bias, overlapping pair windows are not used, to the number of pair-similarities computed
    is len(songs)/2.
    This should be as scalable as possible with large song lists.
    """
    #filter(song__in=songs) will not work on sqlite with more than 999 songs, so it has to be broken to pieces
#    Song_progression_count.objects.filter(song__in=songs)
    song_progression_links = list()
    bulk_size = 999
    for i in range(len(songs)/bulk_size + 1):
        with transaction.commit_on_success():
            song_progression_links.extend(Song_progression_count.objects.filter(song__in=songs[i*bulk_size:(i+1)*bulk_size]))
    #same thing about this part
    progression_counts = dict()
    for i in range(len(song_progression_links)/bulk_size + 1):
        with transaction.commit_on_success():
            progression_counts.update({(song_progression_link.song,song_progression_link.progression):\
                                       song_progression_link.appearance_count\
                                       for song_progression_link in song_progression_links[i*bulk_size:(i+1)*bulk_size]})
    average_similarity = 0
    for i in range(len(songs)/2):
        first_progression_counts = {progression:appearance_count for (song,progression),appearance_count\
                                     in progression_counts.items() if song==songs[i*2]}
        second_progression_counts = {progression:appearance_count for (song,progression),appearance_count\
                                     in progression_counts.items() if song==songs[i*2 + 1]}
        denominator = float(sum(count for count in first_progression_counts.values()) + \
              sum(count for count in second_progression_counts.values()))/2
        nominator = sum(min(first_progression_counts[progression],second_progression_counts[progression]) \
                for progression in set(first_progression_counts.keys()).intersection(second_progression_counts.keys()))
        average_similarity += (nominator/denominator)/(len(songs)/2)
    return average_similarity

#if __name__ == "__main__":    
#    songs = Song.objects.filter(chords__isnull=False).distinct()[:10]
    #for i in range(len(songs)):
    #    for j in range(i+1,len(songs)):
    #        song = songs[i]
    #        other_song = songs[j]
    #        songs_similarity = similarity(song,other_song)
    #        if songs_similarity >= 0.35:
    #            print song,other_song, songs_similarity
#    print compute_similarity_matrix_bulk(songs)
#    print songs[6],songs[4],similarity(songs[6],songs[4])
#    x= set(songs[6].progressions.all()).intersection(songs[4].progressions.all()).pop()
#    print x