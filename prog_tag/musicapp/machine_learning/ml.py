
from ml_algorithms_test import getMusicData, test_and_print
from sklearn.multiclass import OneVsRestClassifier
from sklearn.metrics import classification_report
from sklearn.naive_bayes import GaussianNB

import pickle 

path_to_classifier = "C:\\Users\\bruchim\\Desktop\\bruner"

#Train a classifier (currently GaussianNB, but may be changes after testing other algorithms)
#Then, save classifier with pickle
def train():
    #when we have a way of loading train data from the db, it will go here
    X, y = getMusicData("train")
    
    clf = OneVsRestClassifier(GaussianNB())
    clf.fit(X, y)
    
    pickle.dump(clf, open(path_to_classifier, 'w'))
    
    
#Test the classifier and print results
def test():
    #when we have a way of loading test data from the db, it will go here
    X_test, y_test = getMusicData("test")
    
    #loading the trained classifier with pickle, and test it with the test data
    #the predicted lables should be translated into actual tags and sent back to the user
    clf = pickle.load(open(path_to_classifier, 'r'))
    predicted = clf.predict(X_test)
    
    #print a report with precision and recall for the given test data
    cr = classification_report(y_test, predicted)
    print cr
    
#Predict the lables for a new, unknown song
#The input is a frequency vector, and the output is a list of labels 
#(currently returns a list of lists of indexes, should be translated into tags from the db, once we have them)
def predict(song_freq_vector):
    
    #loading the trained classifier with pickle, and using it to predict the labels of the given song.
    #the predicted lables should be translated into actual tags and sent back to the user
    clf = pickle.load(open(path_to_classifier, 'r'))
    predicted = clf.predict(song_freq_vector)
    
    #TODO: first translate prediction to actual tags, and then return them
    print predicted
    