'''
Created on Jan 25, 2014

@author: bruchim
'''


import numpy as np

from sklearn.multiclass import OneVsRestClassifier
from sklearn.svm import SVC
from sklearn import neighbors
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier    

from sklearn.metrics import classification_report
from sklearn.metrics import hamming_loss
from sklearn.metrics import accuracy_score

all_target_names = ["US 60s 70s Rock and Pop","dance","Smooth Jazz","pop","Freddie Jackson","heavy metal","Elvis Presley","hard rock","John Denver","classic rock","Surf",
                    "pop rock","killler oldies","baroque pop","piano","20th Century","Classic  Rock","jazz","80ROCK","Disco","instrumental","soft rock","singer-songwriter",
                    "funk","northern soul","soul","morning","garage","rock","50s","classic country","cher","a very special love song","ann","crossover","new wave","blues",
                    "marie osmond","folk","90s","oldies","blues rock","memories","motown","female vocalists","1961","Female country","doo wop","country pop","80s","rhythm and blues",
                    "christmas","paul mccartney","reggae","latin","My all time favourite song","60s","love her music","james taylor","usa hot country songs number one hit","rockabilly",
                    "70s","Hip-Hop","xtph early","female vocalist","country","metal","Psychedelic Rock","Girl Groups","Progressive rock","Superman" ]
    
four_target_names = ["US 60s 70s Rock and Pop","dance","Smooth Jazz","pop"]

"""
Run different ML algorithms, and print their scores on the the same data
"""
def test_ML_algorithms():
    
    """
    Get X, y for both the train data and test data. 
    X = all features (chord proggressions). rows=items, columns=features.  
    y = all lables (music tags & generes). rows=items, columns=lables.
    """
    X, y = getMusicData("train")
    X_test, y_test = getMusicData("test")
    
    
    """
    Test the following Machine Learning algorithms: 
            Nearest Neighbors, Linear SVM, RBF SVM, 
                        Decision Tree, Random Forest, AdaBoost, Naive Bayes
    """
    
    print "TESTING K Nearest Neighbors"
    for weights in ['uniform', 'distance']:
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
    hl = hamming_loss(y_test, predicted, all_target_names)
    
    """
    In multilabel classification, this function computes subset accuracy:
    the set of labels predicted for a sample must *exactly* match the
    corresponding set of labels in y_test.
    """
    ac = accuracy_score(y_test,predicted)
    
    """Print precision, recall, f1-score & support, for all labels."""
    cr = classification_report(y_test, predicted, target_names=all_target_names)

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
Given a matrix y, (rows are different items in the dataset, and columns are different features),
Create a list of lists, a list per each item holds all indexes of the feature it has in the dataset
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


