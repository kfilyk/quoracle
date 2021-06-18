import os
import json
import subprocess
from Scraper import Scraper


class TwitterScraper(Scraper):
    def __init__(self):
        self.mapper_dict = {
            "content": lambda payload: payload.get("content"),
            "source": lambda payload: "twitter",
            "author": lambda payload: payload.get("user")
        }

        # 2020-06-01 - 2020-06-02: means from june 1st at 00:00 to 23:59
        # self.query = "snscrape --jsonl --max-results 100 --since 2020-06-01 twitter-search 'from:elonmusk until:2020-06-02'"
        # self.query = "snscrape --jsonl --max-results 100 --since 2020-06-01 twitter-search '#cocacola until:2020-06-02'"
        # --max-results 100
        self.query = "snscrape --jsonl  --since 2020-06-01 twitter-search '$TSLA until:2020-06-02'"

    def _append_token(self, input_str):
        if (input_str == ""):
            return "{}"
        else:
            return input_str + "}"

    def scrape(self):
        twitter_results = subprocess.check_output(
            self.query, shell=True).decode('utf-8')
        results_list = twitter_results.split('}\n')
        results_list = list(map(self._append_token, results_list))
        discarded_data = results_list.pop()
        # print(results_list)

        extracted_json = list(
            map(lambda json_str: json.loads(json_str), results_list))
        # extracted_content = self.extract_data(results_list)

        def extract_likes(json):
            try:
                # Also convert to int since update_time will be string.  When comparing
                # strings, "10" is smaller than "2".
                return int(json['likeCount'])
            except KeyError:
                return 0

        # lines.sort() is more efficient than lines = lines.sorted()
        extracted_json.sort(key=extract_likes, reverse=True)
        print(extracted_json[0])  # print first tweet, for reference
        print("NUMBER OF TWEETS: ", len(extracted_json))
        i = 1
        for t in extracted_json:
            users_str_list = ""
            if ('mentionedUsers' in t) and (t['mentionedUsers'] != None):
                for u in t['mentionedUsers']:
                    users_str_list = users_str_list + u['username']+", "

            print("%d. | LIKES: %s | HASHTAGS: %s | MENTIONED: %s | ORIGINAL: %s \n %s\n" %
                  (i, t['likeCount'], t['hashtags'], users_str_list, t['url'], t['content']))

            # print(extracted_json[i]['content'])
            i = i+1
        return extracted_json


ts = TwitterScraper()
data = ts.scrape()
# print(data)
