import numpy as np
import pickle
 
from musicapp.models import *
from ml import compute_tag_indices_lists,compute_frequency_vectors_bulk
from musicapp.machine_learning.ml import path_to_selected_tags
from sklearn.metrics.cluster import normalized_mutual_info_score

def feature_selection():
    num_leading_progressions = 3000
    num_selected_features = 200
    songs_list = Song.objects.filter(progressions__isnull=False).filter(tags__isnull=False).distinct()
    leading_progressions = get_leading_progressions(num_leading_progressions)
    
    feature_matrix = get_features_data(leading_progressions,songs_list)
    all_labels_lists = get_label_data(songs_list)
    num_labels = len(all_labels_lists)
    
    selected_features = np.zeros(num_leading_progressions)
    for p in range(num_leading_progressions):
        mi_results = np.zeros(num_labels)
        
        for l in range(num_labels):
            mi = normalized_mutual_info_score(feature_matrix[p], all_labels_lists[l])
            mi_results[l] = mi
        
        avg_mi = np.average(mi_results) 
        selected_features[p] = avg_mi
        
    highest_mi_feature_indices = np.argsort(selected_features)[num_leading_progressions-num_selected_features-1:num_leading_progressions]
    return [leading_progressions[i] for i in highest_mi_feature_indices]

def get_mi_with_mock():
    progression, label = make_mock_data()
    mi = normalized_mutual_info_score(progression, label)
    print mi


def make_mock_data():
    num_of_songs = 100000
    progression_per_song = np.zeros(num_of_songs, dtype=np.int)
    label_per_song = np.zeros(num_of_songs, dtype=np.int)
    for i in range(num_of_songs):
        if i%5:
            progression_per_song[i] = i
            label_per_song[i] = 1
            
    return progression_per_song, label_per_song

def get_label_data(songs_list):
    leading_tags = pickle.load(open(path_to_selected_tags,'r'))
    all_labels_lists = [[] for _dummy in xrange(len(leading_tags))]
    for song in songs_list:
        song_tags = song.tags.all()
        all_labels_lists[song] = [i for i,tag in enumerate(leading_tags) if tag in song_tags]
        
def get_features_data(leading_progressions,song_list):
    #create a "frequenct matrix", which will be the input of the feature selection process 
    feature_matrix = compute_frequency_vectors_bulk(song_list, leading_progressions, threshold = 0.5)
    return feature_matrix
  
    
def get_leading_progressions(number_of_progressions):
    #return the number_of_progressions leading progressions, by number of appearances in songs
    progression_list_index = Chord_progression.objects.count() - number_of_progressions
    leading_progressions = list(Chord_progression.objects.all().order_by('appearances')[progression_list_index:])
    return leading_progressions


get_mi_with_mock()