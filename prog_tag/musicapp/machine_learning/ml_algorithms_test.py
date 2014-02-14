
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
from musicapp.machine_learning.ml import path_to_selected_tags, path_to_frequency_matrix

"""
Run different ML algorithms, and print their scores on the the same data
"""
def test_ML_algorithms():
    
    """
    Get X, y for both the train data and test data. 
    X = all features (chord proggressions). rows=items, columns=features.  
    y = all lables (music tags & generes). rows=items, columns=lables.
    """
    songs_with_data = Song.objects.filter(progressions__isnull=False).filter(tags__isnull=False).distinct()
    leading_tags_set = set(pickle.load(open(path_to_selected_tags,'r')))
    songs_with_data = [song for song in songs_with_data if leading_tags_set.intersection(song.tags.all())]
    tag_indices_lists = compute_tag_indices_lists(songs_with_data)
#    frequency_matrix = compute_frequency_vectors_bulk(songs_with_data)
    frequency_matrix = pickle.load(open(path_to_frequency_matrix,'r'))
    split_index = int(len(songs_with_data)*0.8)

    X, y = frequency_matrix[:split_index,:], tag_indices_lists[:split_index]
    X_test, y_test = frequency_matrix[split_index:,:], tag_indices_lists[split_index:]
    
    
    """
    Test the following Machine Learning algorithms: 
            Nearest Neighbors, Linear SVM, RBF SVM, 
                        Decision Tree, Random Forest, AdaBoost, Naive Bayes
    """
    
    print "TESTING K Nearest Neighbors"
    for weights in ['uniform', 'distance']: #read about kmean, and be aware that many features (>=50) will lead to bad results
        test_and_print(X, y, X_test, y_test, 
                       neighbors.KNeighborsClassifier(n_neighbors = 1, weights=weights))
        
    print "TESTING Linear SVM"
    test_and_print(X, y, X_test, y_test, SVC(kernel="linear", C=0.025))
    
    print "TESTING RBF SVM"
    test_and_print(X, y, X_test, y_test, SVC(gamma=2, C=1))

    print "TESTING Decision Tree"
    test_and_print(X, y, X_test, y_test, DecisionTreeClassifier(max_depth=5))

    print "TESTING Random Forest"
    test_and_print(X, y, X_test, y_test, RandomForestClassifier(max_depth=5, n_estimators=10, max_features=1))

    print "TESTING AdaBoost"
    test_and_print(X, y, X_test, y_test, AdaBoostClassifier())
    
    print "TESTING Naive Bayes"
    test_and_print(X, y, X_test, y_test, GaussianNB())
        

def test_and_print(X, y, X_test, y_test, clf):
    
    """
    Create a Multilabel version of the classifier (one classifier per label).
    Train the classifier with the training data,
    Then, predict the outcome of the test data. 
    """
    clf = OneVsRestClassifier(clf)
    clf.fit(X, y)
    predicted = clf.predict(X_test)
    
    """Start applying different metrics on the classifier results: Hamming loss, Accuracy score, Classification report"""
    
    """The Hamming loss is the fraction of labels that are incorrectly predicted."""
    hl = hamming_loss(y_test, predicted, [tag.name for tag in pickle.load(open(path_to_selected_tags,'r'))])
    
    """
    In multilabel classification, this function computes subset accuracy:
    the set of labels predicted for a sample must *exactly* match the
    corresponding set of labels in y_test.
    """
    ac = accuracy_score(y_test,predicted)
    
    """Print precision, recall, f1-score & support, for all labels."""
    cr = classification_report(y_test, predicted, target_names=\
                               [tag.name for tag in pickle.load(open(path_to_selected_tags,'r'))])

    print "---------------------------------------------------------"
    print "Hamming Loss = "+ str(hl)
    print "Accuracy Score = "+str(ac)
    print "Classification Report = "+str(cr)
    
"""
Read CSV files into an array.
Each call reads a features file and a labels file
"""
def getMusicData(tr_ts):
    
    music_data_features = np.genfromtxt('C:/Users/bruchim/Desktop/all_'+tr_ts+'_features.csv', delimiter=',', dtype= 'float')
    music_data_labels = np.genfromtxt('C:/Users/bruchim/Desktop/all_'+tr_ts+'_labels.csv', delimiter=',')
    
    X = music_data_features
    y = makeMultiLabelVector(music_data_labels)    
    return X, y


"""
Given a matrix y, (rows are different items in the dataset, and columns are different labels),
Create a list of lists, a list per each item holds all indexes of the label it has in the dataset
"""
def makeMultiLabelVector(y):
    items, features = y.shape
    new_y = [[] for _dummy in xrange(items)]
    for i in range(items):     
        for j in range(features):  
            if (y[i][j]==1): new_y[i].append(j)
    return new_y


"""
Given a matrix y, (rows are different items in the dataset, and columns are different features),
Create a single 1D vector, each item gets the index of the *first* feature it has in the dataset 
This is used just for checking the normal (not nultilabel) version of algorithms

def makeClassesVector(y):
    items, features = y.shape
    new_y = np.zeros(items)
    for i in range(items):     
        for j in range(features):  
            
            if (y[i][j]==1):
                new_y[i] = j+1
                break
    return new_y
"""

test_ML_algorithms()
