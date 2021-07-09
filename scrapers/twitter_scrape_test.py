import json
import subprocess
from datetime import datetime


def get_likes(json):
    try:
        # Also convert to int since update_time will be string.  When comparing
        # strings, "10" is smaller than "2".
        return int(json['likeCount'])
    except KeyError:
        return 0


def append_token(str):
    if (str == ""):
        return "{}"
    else:
        return str + "}"


def call_snscrape(query):

    twitter_results = subprocess.check_output(
        query, shell=True).decode('utf-8')
    results_list = twitter_results.split('}\n')
    results_list = list(map(append_token, results_list))
    results_list.pop()
    extracted_json = list(
        map(lambda json_str: json.loads(json_str), results_list))

    for t in extracted_json:  # filter to get only english tweets
        if(t['lang'] != 'en'):
            extracted_json.remove(t)
        # if(detect(t['content']) != 'en'):
        #    extracted_json.remove(t)
    extracted_json.sort(key=get_likes, reverse=True)
    return extracted_json


extracted_json = call_snscrape(
    "snscrape --jsonl twitter-search 'from:alpine4holdings'")

print(extracted_json)
