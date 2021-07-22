from collections import Counter
import os
from os import listdir, walk
from os.path import isfile, join
import json
dict_file_path = './dict.csv'
meta_data_path = './meta_data.txt'
scraped_data_file_path = './scraped_data/'
scraped_data_files = []
for (dirpath, dirnames, filenames) in walk(scraped_data_file_path):
    for fi in filenames:
        if '.json' in fi:
            print(dirpath)
            scraped_data_files.append(dirpath + '/'+fi)
print(scraped_data_files)


for fi in scraped_data_files:
    if os.path.isfile(fi):
        with open(fi) as f:
            for jsonObj in f:
                j = json.loads(jsonObj)
                for d in j:
                    if d != 'url' and d != 'conversation_id':
                        print(d)
                break
'''
scraped_data_files = [f for f in listdir(scraped_data_file_path) if isfile(
    join(scraped_data_file_path, f))]  # file path of count ordered dict
print(scraped_data_files)

'''
