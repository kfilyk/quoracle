from collections import Counter
import os
from os import listdir, walk
from os.path import isfile, join
import json
dict_file_path = './dict.csv'
meta_data_path = './meta_data.txt'
scraped_data_file_path = './data/raw/'
encoded_data_file_path = './data/encoded/'
scraped_data_files = []
for (dirpath, dirnames, filenames) in walk(scraped_data_file_path):
    for fi in filenames:
        if '.json' in fi:
            # print(dirpath)
            scraped_data_files.append(dirpath + '/'+fi)
# print(scraped_data_files)

all_words = []
convos = []
for fi in scraped_data_files:
    if os.path.isfile(fi):
        with open(fi) as f:
            for jsonObj in f:  # for every conversation
                j = json.loads(jsonObj)
                for d in j:
                    if d != 'url' and d != 'conversation_id':  # get only time
                        words = j[d]['content'].split()
                        for w in words:
                            all_words.append(w)
                        # print("%s: %s" % (d, j[d]['content'])) # print content
                # print('\n')

count_words = Counter(all_words)
total_words = len(all_words)
sorted_words = count_words.most_common(total_words)

vocab_to_int = {w: [i, c] for i, (w, c) in enumerate(sorted_words)}
print(vocab_to_int)
'''
scraped_data_files = [f for f in listdir(scraped_data_file_path) if isfile(
    join(scraped_data_file_path, f))]  # file path of count ordered dict
print(scraped_data_files)

'''

encoded_convos = []
for review in reviews_split:
    r = [vocab_to_int[w] for w in review.split()]
    reviews_int.append(r)
print(reviews_int[0:3])
