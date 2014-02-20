import numpy as np
import pickle
 
from musicapp.models import *
from ml import compute_tag_indices_lists,compute_frequency_vectors_bulk
from musicapp.machine_learning.ml import path_to_selected_tags, path_to_selected_progressions
from sklearn.metrics.cluster import normalized_mutual_info_score


"""
1. Filter out rare chord progressions
2. Calculate Mutual information for all chord progressions-label pairs
3. Avarge MI results for each progression across all labels, and select the top as ML features
"""
def feature_selection():
    num_leading_progressions = 900
    num_selected_features = 50
    songs_list = Song.objects.filter(progressions__isnull=False).filter(tags__isnull=False).distinct()
    
    leading_progressions = get_leading_progressions(num_leading_progressions)
    
    feature_matrix = get_features_data(leading_progressions,songs_list)
    all_labels_lists = get_label_data(songs_list)
    num_labels = len(all_labels_lists)
    
    selected_features = [np.empty((num_selected_features), dtype=object) for _i in xrange(num_labels)]
    for l in range(num_labels):
        mi_results = np.zeros(num_leading_progressions)
            
        for p in range(num_leading_progressions):
            mi = normalized_mutual_info_score(feature_matrix[:,p], all_labels_lists[l])
            mi_results[p] = mi
            
        highest_mi_feature_indices = np.argsort(mi_results)[num_leading_progressions-num_selected_features:]
        selected_features[l] = [leading_progressions[i] for i in highest_mi_feature_indices]
        
    pickle.dump(selected_features,open(path_to_selected_progressions,'w'))
    

def get_label_data(songs_list):
    leading_tags = pickle.load(open(path_to_selected_tags,'r'))
    all_labels_lists = [np.zeros(len(songs_list)) for _dummy in xrange(len(leading_tags))]
    for tag_index, leading_tag in enumerate(leading_tags):
        for song_index, song in enumerate(songs_list):
            song = songs_list[song_index]
            song_tags = song.tags.all()
            if leading_tag in song_tags: all_labels_lists[tag_index][song_index] = 1
    return all_labels_lists
        
def get_features_data(leading_progressions,song_list):
    #create a "frequenct matrix", which will be the input of the feature selection process 
    feature_matrix = compute_frequency_vectors_bulk(song_list, leading_progressions, threshold = 0.0001)
    return feature_matrix
  
    
def get_leading_progressions(number_of_progressions):
    #return the number_of_progressions leading progressions, by number of appearances in songs
    progression_list_index = Chord_progression.objects.count() - number_of_progressions
    leading_progressions = list(Chord_progression.objects.all().order_by('appearances')[progression_list_index:])
    return leading_progressions

feature_selection()