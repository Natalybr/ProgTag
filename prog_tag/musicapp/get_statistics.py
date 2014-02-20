from musicapp.models import *
from django.db.models import Sum,Count
from musicapp.metric.metric import *
import random
from common_tasks import time_elapsed_minutes
from musicapp.common_tasks import time_elapsed_minutes
import time
from collections import Counter
from django.db import transaction

for song in Song.objects.filter(chords__isnull=False).distinct():
    if '&' in song.artist:
        with transaction.commit_on_success():
            for index in Song_chord_index.objects.filter(song=song): index.delete()
            for index in Song_progression_count.objects.filter(song=song):
                progression = index.progression
                progression.appearances -= index.appearance_count
                progression.save()
                index.delete()


print 'number of songs', Song.objects.count()
print 'number of songs with tags', Song.objects.filter(tags__isnull=False).distinct().count()
print 'number of songs with chords and tags', Song.objects.filter(tags__isnull=False, chords__isnull=False).distinct().count()

print 'number of unique progressions', Chord_progression.objects.count()
print 'average number of chords for song with chords', float(Song_chord_index.objects.count())/\
    Song.objects.filter(chords__isnull=False).distinct().count()
print 'average number of progressions for song with chords (counting #appearances)', \
    float(Chord_progression.objects.aggregate(Sum('appearances')).values()[0])/\
        Song.objects.filter(chords__isnull=False).distinct().count()
print 'average number of progressions for song with chords (not counting #appearances)', \
    float(Song_progression_count.objects.count())/\
        Song.objects.filter(chords__isnull=False).distinct().count()
        

print 'number of tags', Tag.objects.count()
print 'average number of tags for song with tags', float(Song.objects.filter(tags__isnull=False).count())/ \
    Song.objects.filter(tags__isnull=False).distinct().count()

#compute progression appearance histogram
progression_histogram = dict()
for progression in Chord_progression.objects.all():
    progression_histogram[progression.appearances] = progression_histogram.get(progression.appearances,0) + 1
with open('./progression_histogram','w') as output_file:
    for i in range(1,max(progression_histogram.keys())+1):
        output_file.write(str(i) + ',' + str(progression_histogram.get(i,0)) + '\n')

#compute tag appearance histogram
tag_histogram = dict()
for tag in Tag.objects.annotate(appearances=Count('song')):
    tag_histogram[tag.appearances] = tag_histogram.get(tag.appearances,0) + 1
with open('./tag_histogram','w') as output_file:
    for i in range(1,max(tag_histogram.keys())+1):
        output_file.write(str(i) + ',' + str(tag_histogram.get(i,0)) + '\n')
   
#compute average similarity between different songs
#songs_with_chords = Song.objects.filter(progressions__isnull=False).distinct().\
#    order_by('?')[:5] #don't order by random! bugs filtering later (filter song__in)
#matrix_number_of_samples = 200
#songs_with_chords = Song.objects.filter(progressions__isnull=False).distinct()
#sampled_songs = random.sample(songs_with_chords, matrix_number_of_samples)
#similarity_matrix = compute_similarity_matrix_bulk(sampled_songs)
#average = (similarity_matrix.mean() - 1.0/len(songs_with_chords))*((len(songs_with_chords)**2)/(len(songs_with_chords)*(len(songs_with_chords)-1)))
#print 'average similarity between different songs with chords (matrix):',average
number_of_samples = 200
average_of_averages = 0
number_of_iterations = 2
for i in range(number_of_iterations):
    start_time = time.time()
    songs_with_chords = Song.objects.filter(progressions__isnull=False).distinct()
    sampled_songs = random.sample(songs_with_chords, number_of_samples)
    average = compute_average_similarity_between_adjacent_pairs(sampled_songs)
    print 'average similarity between different songs with chords (pairwise sampling):',average,'time taken:', \
        time_elapsed_minutes(start_time)
    start_time = time.time()
    average_of_averages += average/number_of_iterations 
print 'average of all averages (no constraints):', average_of_averages

#compute average similarity between different songs with same artist
number_of_artists_sampled = 100
#artists = Song.objects.filter(progressions__isnull=False).distinct().values_list('artist', flat=True).\
#                annotate(c=Count('artist')).filter(c__ge=10) #does NOT produce wanted results, and I have no idea why.
artist_appearance_counts = dict()
for song in Song.objects.filter(progressions__isnull=False).distinct():
    artist_appearance_counts[song.artist] = artist_appearance_counts.get(song.artist,0) + 1
artists = [artist for artist in artist_appearance_counts if artist_appearance_counts[artist] >= 10]
#print len(artists)
average_of_averages = 0

for artist in random.sample(artists,number_of_artists_sampled):
    start_time = time.time()
    songs = Song.objects.filter(artist=artist).filter(progressions__isnull=False).distinct()
    artist_average = compute_average_similarity_between_adjacent_pairs(songs) 
    #does not compute similarity of song with itself, so *should* be unbiased towards artists with less songs.
#    print 'artist:', artist,'number of songs:',len(songs),'average_similarity:',artist_average,'time taken:', \
#        time_elapsed_minutes(start_time)
    start_time = time.time()
    if artist_average > 0.5: print artist, artist_average
    average_of_averages += artist_average / number_of_artists_sampled
print 'average of all averages (same artist):', average_of_averages

#compute average similarity between different songs with same tag (use only leading tags)
number_of_tags_sampled = 10
tag_list_index = Tag.objects.count() - number_of_tags_sampled
tags = list(Tag.objects.annotate(song_count=Count('song')).order_by('song_count')[tag_list_index:])
song_samples = 300
average_of_averages = 0
for tag in tags:
    start_time = time.time()
    songs = Song.objects.filter(tags=tag).filter(progressions__isnull=False).distinct() # no need for distinct() on tag filter
    #sampling because this might be huge
    songs = random.sample(songs, min([song_samples, len(songs)]))
    tag_average = compute_average_similarity_between_adjacent_pairs(songs) 
    #does not compute similarity of song with itself, so *should* be unbiased towards tags with less songs.
    print 'tag:', tag,'number of songs tested:',len(songs),'average_similarity:',tag_average, 'time taken:',\
        time_elapsed_minutes(start_time)
    start_time = time.time()
    average_of_averages += tag_average / number_of_tags_sampled
print 'average of all averages (same tag):', average_of_averages
    
