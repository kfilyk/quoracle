import os
tweets = os.system(
    "snscrape --jsonl --max-results 100 twitter-search 'from:elonmusk'")
print(tweets)
