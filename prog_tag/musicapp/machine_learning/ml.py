
from sklearn.multiclass import OneVsRestClassifier
from sklearn.metrics import classification_report
from sklearn.naive_bayes import GaussianNB
from musicapp.models import *
from sklearn.metrics import precision_recall_fscore_support
import numpy
import pickle 
from django.db.models import Count
import time
from musicapp.common_tasks import *

path_to_classifier = "./classifier"
path_to_selected_tags = "./tags"
path_to_selected_progressions = "./progressions"
path_to_frequency_matrix = "./matrix"

def select_leading_tags(number_of_tags):
    """select the number_of_tags leading tags, by number of songs tagged by them, and save them for future ML operations"""
    tag_list_index = Tag.objects.count() - number_of_tags
    leading_tags = list(Tag.objects.annotate(song_count=Count('song')).order_by('song_count')[tag_list_index:])
#    print leading_tags
    pickle.dump(leading_tags,open(path_to_selected_tags,'w'))
    
def select_leading_progressions(number_of_progressions):
    """select the number_of_progressions leading progressions, by number of appearances in songs, 
    and save them for future ML operations"""    
    progression_list_index = Chord_progression.objects.count() - number_of_progressions
    leading_progressions = list(Chord_progression.objects.all().order_by('appearances')[progression_list_index:])
#    print leading_progressions
    pickle.dump(leading_progressions,open(path_to_selected_progressions,'w'))

def compute_frequency_vector(song, leading_progressions = None):
    """for a given song, assuming leading progressions are already pickled, compute the vector of their frequencies in it.
    The i'th value is the number of appearances of the i'th progression in the song, divided by (len(song)//len(progression)),
    so it is always in range [0,1] (progressions are counted without overlap).
    leading_progression is an optional parameter, designed to skip the unpickling process, in case of frequent iterative calls."""
    if not leading_progressions: leading_progressions = pickle.load(open(path_to_selected_progressions,'r'))
    frequency_vector = [0]*len(leading_progressions)
    for i,progression in enumerate(leading_progressions):
        appearances = Song_progression_count.objects.get(song=song, progression=progression).appearance_count \
            if Song_progression_count.objects.filter(song=song, progression=progression).count() else 0
        song_length = Song_chord_index.objects.filter(song=song).count()
        frequency_vector[i] = float(appearances) / (song_length // progression.length)
    return frequency_vector

def compute_frequency_vectors(song_list):
    leading_progressions = pickle.load(open(path_to_selected_progressions,'r'))
    frequency_matrix = numpy.zeros((len(song_list),len(leading_progressions)))
    #could be optimized by doing less querying and more processing here, instead of calling compute_frequency_vector for 
    #each song individually. If this proves to be a bottleneck, this might be a fix.
    for i,song in enumerate(song_list):
        song_vector = compute_frequency_vector(song, leading_progressions)
        frequency_matrix[i] = song_vector
        if i and not i%1000: print "done for",i,"songs!"
    return frequency_matrix

def compute_frequency_vectors_bulk(song_list):
    leading_progressions = pickle.load(open(path_to_selected_progressions,'r'))
    song_lengths = [song.chords.count() for song in song_list]
    frequency_matrix = numpy.zeros((len(song_list),len(leading_progressions)))
    progress = 0
    
    start_time = time.time()
    with transaction.commit_on_success():
        appearances = {song: Song_progression_count.objects.filter(song=song,progression__in=leading_progressions)\
                       for song in song_list}
    print 'appearances dict computed in', time_elapsed_minutes(start_time)
    
    progressions_to_indices = {b:a for a,b in enumerate(leading_progressions)}
    for song_index, song in enumerate(song_list):
        for appearance in appearances[song]:
            progression_index = progressions_to_indices[appearance.progression]
            frequency_matrix[song_index,progression_index] = \
                float(appearance.appearance_count) / (song_lengths[song_index] // appearance.progression.length)
    
#    for prog_index,progression in enumerate(leading_progressions):
#        for song_index,song in enumerate(song_list):
#            appearances = Song_progression_count.objects.get(song=song, progression=progression).appearance_count \
#                if Song_progression_count.objects.filter(song=song, progression=progression).count() else 0
#            frequency_matrix[song_index,prog_index] = float(appearances) / (song_lengths[song_index] // progression.length)
#        progress += 1
#        if not progress % 10 : print 'covered', progress, 'progressions.'
    return frequency_matrix


def compute_tag_indices_list(song, leading_tags = None):
    """for a given song, assuming leading tags are already pickled, compute a list of indices of tags that the song has,
    using the ordering of the leading_tags list.    
    leading_tags is an optional parameter, designed to skip the unpickling process, in case of frequent iterative calls."""
    if not leading_tags: leading_tags = pickle.load(open(path_to_selected_tags,'r'))  
    song_tags = song.tags.all()
    return [i for i,tag in enumerate(leading_tags) if tag in song_tags]


def compute_tag_indices_lists(song_list):
    leading_tags = pickle.load(open(path_to_selected_tags,'r'))
    return [compute_tag_indices_list(song,leading_tags) for song in song_list]
    
def build_classifier_for_database():
    #prepare data
    songs_with_data = Song.objects.filter(progressions__isnull=False).filter(tags__isnull=False).distinct()
#    print 'preparing frequency matrix for', len(songs_with_data), "songs."
#    frequency_matrix = compute_frequency_vectors_bulk(songs_with_data)
    frequency_matrix = pickle.load(open(path_to_frequency_matrix,'r'))
    print 'preparing tag lists'
    tag_indices_lists = compute_tag_indices_lists(songs_with_data)
    
    print 'training testing classifiers'
    #do repeated iterations of machine learning on different train-test permutations of the data, to get valid statistics
    number_of_test_iterations = 200
    average_statistics = [0,0,0]#precision, recall, fscore
    start_time = time.time()
    for i in range(number_of_test_iterations): 
        #shuffle data
        permutation = numpy.arange(len(songs_with_data))
        numpy.random.shuffle(permutation)
        shuffled_matrix = frequency_matrix[permutation]
        shuffled_tag_lists = [tag_indices_lists[i] for i in permutation]
        
        #send first 80% to training, last 20% to testing
        split_index = int((0.8*len(songs_with_data)))
        classifier = train_classifier(shuffled_matrix[:split_index], shuffled_tag_lists[:split_index])
        statistics = test_classifier(shuffled_matrix[split_index:], shuffled_tag_lists[split_index:], classifier,\
                                     result_average = True) #regular output is of varied length, the number of labels vectors have
#        print statistics
        for i in range(3): average_statistics[i] += statistics[i]/number_of_test_iterations
#        average_statistics[3] = [x + y/1000 for x,y in zip(average_statistics[3], statistics[3])]#no support for averaging
        if not (i+1)%10: 
            print 'trained and tested', i, 'classifiers. Time taken:', time_elapsed_minutes(start_time)
            start_time = time.time()
    #print statistics
    print 'training statistics: precision={:.2},recall={:.2},fscore={:.2}.'.format(*average_statistics)
    
    #train final classifier on all data
    classifier = train_classifier(frequency_matrix, tag_indices_lists)
    print 'trained final classifier on whole data. Printing statistics for each tag classifier:'
    statistics = test_classifier(frequency_matrix, tag_indices_lists, classifier, result_average=False)
    for tag_index,tag in enumerate(pickle.load(open(path_to_selected_tags,'r'))):
        tag_statistics = [statistics[i][tag_index] for i in range(4)]
        print 'For tag "{}", precision={:.2},recall={:.2},fscore={:.2},support={}.'.format(tag.name,*tag_statistics)
    pickle.dump(classifier, open(path_to_classifier,'w'))
    
    print 'done.'

"""Train a classifier (currently GaussianNB, but may be changes after testing other algorithms) on a given data and return
    the resulting classifier. The data is assumed to be formatted as following - 
    X - a numpy 
    """
def train_classifier(X,y):
    classifier = OneVsRestClassifier(GaussianNB())
    classifier.fit(X, y)
    return classifier

"""
    Given a classifier and labeled data, test the classifier's predictions on the data and output their values.
    X and y are assumed to be formatted as in train_on_data. 
    There are two output formats, depending on the 'result_average' parameter. 
    If True: Output is a (precision, recall, fscore, None) tuple, where the values are averaged over the individual label
    classifiers, with weighting according to the corresponding supports.
    If False: Output is a tuple of length 4. The members of the tuple are numpy arrays with length as the number of unique
    labels the input vectors possessed. The first array corresponds to precision values for each label, etc.
"""
def test_classifier(X,y,classifier,result_average=True):
    predicted = classifier.predict(X)
    result_average = 'weighted' if result_average else None
    number_of_labels = len(pickle.load(open(path_to_selected_tags,'r')))
    return precision_recall_fscore_support(y, predicted, labels=list(range(number_of_labels)),\
                                           pos_label=number_of_labels, average=result_average)    
    

def store_frequency_matrix(song_list):
    pickle.dump(compute_frequency_vectors_bulk(song_list), open(path_to_frequency_matrix,'w'))

if __name__ == "__main__":    
    """testing"""
    select_leading_progressions(150)
    select_leading_tags(20)
    songs_with_data = Song.objects.filter(progressions__isnull=False, tags__isnull=False).distinct()
    store_frequency_matrix(songs_with_data)
    
    print 'found', len(songs_with_data), 'songs with progressions and tags'
    leading_tags_set = set(pickle.load(open(path_to_selected_tags,'r')))
    #print 'filtering down songs to ones with leading tags'
    #songs_with_data = [song for song in songs_with_data if leading_tags_set.intersection(song.tags.all())]
    #print 'done filtering. Left with', len(songs_with_data)
    start_time = time.time()
    build_classifier_for_database()
    print 'done building classifier. Time taken:', time_elapsed_minutes(start_time)