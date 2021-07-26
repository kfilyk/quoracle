
from collections import Counter
from pathlib import Path

import os
from os import listdir, walk
from os.path import isfile, join
import json

scraped_data_file_path = '../data/raw/'
scraped_data_files = []

file_path = '../data/encoding_dict.json'
encoding_dict = {}
with open(file_path, 'r') as f:
    encoding_dict = json.load(f)  # get the encoding dictionary

for (dirpath, dirnames, filenames) in walk(scraped_data_file_path):
    for fi in filenames:
        if '.json' in fi:
            # print(dirpath)
            scraped_data_files.append(dirpath + '/'+fi)

# collection of scraped data files
for fi in scraped_data_files:
    if os.path.isfile(fi):
        with open(fi, 'r') as f:
            encoded_data = {}
            data = json.load(f)  # json list
            # for every tweet listed
            for tweet in data:
                encoded_tweet = [encoding_dict[w]["count"]
                                 for w in data[tweet].split()]
                encoded_data[tweet] = encoded_tweet
            encoded_data_file_path = fi.replace(
                'raw', 'encoded')
            encoded_data_file_path = encoded_data_file_path.replace(
                'twitter.json', '')
            Path(encoded_data_file_path
                 ).mkdir(parents=True, exist_ok=True)
            with open(encoded_data_file_path+'twitter.json', 'w+') as f2:
                json.dump(encoded_data, f2)  # should
