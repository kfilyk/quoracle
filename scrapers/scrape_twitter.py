import os
import json
import subprocess
query = "snscrape --jsonl --max-results 100 twitter-search 'from:elonmusk'"
# os.system()
tweets = subprocess.check_output(query, shell=True).decode('utf-8')
# print(tweets)
tweet_list = tweets.split('}\n')

tweet_list = list(map(lambda s: s + '}', tweet_list))
print(tweet_list[0])
json_tweets = json.loads(tweets)
