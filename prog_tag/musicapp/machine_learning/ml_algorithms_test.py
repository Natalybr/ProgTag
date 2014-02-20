"""
 Created on Jan 25, 2014
 
 @author: bruchim
"""
 
import numpy as np
import pickle
 
from sklearn.multiclass import OneVsRestClassifier
from sklearn.svm import SVC
from sklearn import neighbors
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier    

from sklearn.metrics import classification_report
from sklearn.metrics import hamming_loss
from sklearn.metrics import accuracy_score

from musicapp.models import *
from ml import compute_tag_indices_lists,compute_frequency_vectors_bulk
from musicapp.machine_learning.ml import path_to_selected_tags, path_to_selected_progressions, precision_recall_fscore_support



path_to_label_matrix_all_labels = "./label_matrix_all_labels"
path_to_feature_matrix_all_labels = "./feature_matrix_all_labels"


def try_all_algorithms_per_label():
    
    try_an_algorithm_per_label(neighbors.KNeighborsClassifier(n_neighbors = 4, weights='uniform'), "KNN")    
            
    try_an_algorithm_per_label(SVC(kernel="linear", C=0.025), "LinearSVM")
    
    try_an_algorithm_per_label(SVC(gamma=2, C=1), "SVM")
    
    try_an_algorithm_per_label(DecisionTreeClassifier(max_depth=5), "DecisionTree")
    
    try_an_algorithm_per_label(RandomForestClassifier(max_depth=5, n_estimators=10, max_features=1), "RandomForest")
    
    try_an_algorithm_per_label(AdaBoostClassifier(), "AdaBoost")
    
    try_an_algorithm_per_label(GaussianNB() , "Naive Bayes")

    
def try_an_algorithm_per_label(clf, name):
    song_list, leading_tags, leading_progressions_by_labels = get_data()
    split_index = int(len(song_list)*0.8)
    
    avg_p = np.zeros(len(leading_progressions_by_labels))
    avg_r = np.zeros(len(leading_progressions_by_labels))
    
    for label_index in range(len(leading_tags)):  
        
        label_matrix = label_matrix_all_labels[label_index]
        feature_matrix = feature_matrix_all_labels[label_index]
        
        X, y = feature_matrix[:split_index,:], label_matrix[:split_index]
        X_test, y_test = feature_matrix[split_index:,:], label_matrix[split_index:]
    
        clf.fit(X, y)
        predicted = clf.predict(X_test)

        p,r,f,s = precision_recall_fscore_support(y_test, predicted, labels=list(range(2)), average="weighted")    
        
        avg_p[label_index] = p
        avg_r[label_index] = r
        
    print name +":     precision = "+str(np.average(avg_p))+":     recall = "+str(np.average(avg_r))


def compute_Y_per_label(song_list, tag):
    y = np.zeros(len(song_list))
    for i, song in enumerate(song_list):
        song_tags = song.tags.all()
        if tag in song_tags: y[i] = 1
    return y


def get_data():
    leading_progressions_by_labels = pickle.load(open(path_to_selected_progressions,'r'))
    songs_with_data = Song.objects.filter(progressions__isnull=False).filter(tags__isnull=False).distinct()
    leading_tags = pickle.load(open(path_to_selected_tags,'r'))
    
    return songs_with_data, leading_tags, leading_progressions_by_labels
    
    
def compute_x_y_all_labels(load=False):
    if load: 
        label_matrix_all_labels = pickle.load(open(path_to_label_matrix_all_labels,'r'))
        feature_matrix_all_labels = pickle.load(open(path_to_feature_matrix_all_labels,'r'))
    else:
        song_list, leading_tags, leading_progressions_by_labels = get_data()
        #compute Y for all labels
        label_matrix_all_labels = [np.zeros(len(song_list)) for _i in xrange(len(leading_tags))]
        #compute X for all labels
        feature_matrix_all_labels = [np.zeros((len(song_list), len(leading_progressions_by_labels[0]))) for _i in xrange(len(leading_tags))]
        
        for label_index, leading_progressions in enumerate(leading_progressions_by_labels):  
            
            label_vector = compute_Y_per_label(song_list, leading_tags[label_index])
            feature_matrix = compute_frequency_vectors_bulk(song_list, leading_progressions)
            
            label_matrix_all_labels[label_index] = label_vector
            feature_matrix_all_labels[label_index] = feature_matrix
            
        
        pickle.dump(label_matrix_all_labels,open(path_to_label_matrix_all_labels,'w'))
        pickle.dump(feature_matrix_all_labels,open(path_to_feature_matrix_all_labels,'w'))
  
    return label_matrix_all_labels, feature_matrix_all_labels

label_matrix_all_labels , feature_matrix_all_labels = compute_x_y_all_labels()
try_all_algorithms_per_label()