"""
This script
- Transforms a training file to the input format required by LibLINEAR.
- Output feature file for prediction.  
=======================================================================

Original training file format, for each line:
label<tab>query
For example:
    1   What do people think of ?
Transformed format, for each line:
label<space>feature index:feature value<space>feature index:feature value
For example:
    2 18:1 24:1 46:1 49:1 50:1 56:1 62:1 71:1 82:1 87:1 94:1
Note: 
- When transforming training file, 
  the feature index should be in strictly ascending order

Usage: refer to "daily_train.py"

Author: Wenjun Wang
Date: June 28, 2015
"""
import pickle
import time
import csv

from feature import *
from liblinearutil import *

class Train(object):
    def __init__(self, train_file, stpfile, features, feature_file, options=''):
        self.stopwords = stopword(stpfile)
        self.feature_arg = parse_options(options)
        self.train_file = train_file
        self.features = features
        self.feature_file = feature_file
        self.feature_list = self._train_feature()

    def _train_feature(self):
        """Extract features from all queries in the training file

        Outcome:
           - Return a list of features
           - Write feature list to output file
        """
        feature_set = set()
        output = open(self.features, 'w')
        for line in open(self.train_file):
            label, query = line.split('\t')
            features = feature_generator(query, self.stopwords, self.feature_arg)
            feature_set |= features

        feature_list = list(feature_set)
        pickle.dump(feature_list, output)

        return feature_list

    def convert_file(self):
        """Transform original training file to the format required by LibLINEAR

        Need:
            self.train_file: the name of the original training file
            self.feature_list: a list of unique features generated by function _train_feature
            self.feature_file: the name of the final transformed file

        Return:
            no return, create a new file, the transformed file
        """
        to_write = []
        for line in open(self.train_file):
            label,query = line.split('\t')
            feature_string = self._convert_query_to_string(query)
            feature_string = label + feature_string + '\n'
            to_write.append(feature_string)

        to_write_string = ''.join(to_write)

        output = open(self.feature_file, 'w')
        output.write(to_write_string)
        output.close()

    def _convert_query_to_string(self, query):
        """Convert each query in the training file to the format required by LibLINEAR

        This function is called by self.convert_file

        Args and Need: 
            query: the raw query, like 'What do people think of ?'
            self.feature_list: a list of unique features generated by function _train_feature
    
        Return:
            Transformed query in string format
        """
        features = feature_generator(query, self.stopwords, self.feature_arg)
        onerow = set()
        for f in features:
            onerow.add(' %s:%s' % (str(self.feature_list.index(f)+1), str(1)))
        onerow = list(onerow)
        onerow.sort(key=lambda feature:int(feature.split(':')[0]))
        feature_string = ''.join(onerow)
    
        return feature_string


def preprocess_trainning_data(raw_file, train_file):
    with open(raw_file, 'r') as f:
        with open(train_file, 'w') as trainning:
            csv_file = csv.reader(f)
            for line in csv_file:
                label, query = line[3], line[1]
                query = query.lower()
                trainning.write(label + '\t' + query + '\n')


def main():
    ### Train Wenjun's classifier
    # Name of files needed when training a model

    date = time.strftime('%Y-%m-%d')
    train_file = 'data/training' # name of original training file
    raw_file = 'data/raw_data'

    feature_file = 'models/training_file_'+date # name of transformed training file
    feature_output = 'models/features_'+date # name of feature file
    stpfile = 'english.stp' # english stopwords file
    feature_arg = '-uni -pos2 -stem -stprm' # types of features need to extract

    preprocess_trainning_data(raw_file, train_file)

    log = open('models/training_log','a') # log file
    log.write('Feature Arguments: %s\n-------------------------------\n'% feature_arg)

    # Create appropriate input file for LibLINEAR (SVM)
    training = Train(train_file, stpfile, feature_output, feature_file, feature_arg)
    training.convert_file()
    # Use LibLINEAR to train the model and save the model
    y, x = svm_read_problem(feature_file)
    m = train(y, x, '-c 3 -s 1 -B 1 -e 0.01 -v 5 -q')
    save_model('models/model_'+date, m)

if __name__ == '__main__':
    main()
