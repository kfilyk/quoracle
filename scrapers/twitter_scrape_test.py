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


"""
tweet = call_snscrape(
    "snscrape --jsonl twitter-search 'Tesla Autonomous Driving Regulatory E-Mails'")
print(tweet)
"""

"""

tweet = call_snscrape(
    "snscrape --jsonl twitter-search 'since_id:1267584909289287679 max_id:1267584909289287681 -filter:safe'")
print(tweet)
"""

conversation = call_snscrape(
    "snscrape --jsonl twitter-search 'conversation_id:1267584909289287680 filter:safe'")

for t in conversation:
    print(t)
    print('\n')


"""

print('\n')

quoted = call_snscrape(
    "snscrape --jsonl twitter-search 'quoted_tweet_id:1267530078688174080 filter:safe'")
for t in quoted:
    print(t)
    print('\n')
print(len(quoted))

"""
