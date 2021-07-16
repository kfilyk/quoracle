import os
import json
import subprocess
from Scraper import Scraper
from langdetect import detect
from datetime import datetime, timedelta
from pathlib import Path
from emoji import UNICODE_EMOJI


def is_emoji(s):
    return s in UNICODE_EMOJI


def add_space(text):
    return ''.join(' ' + char if is_emoji(char) else char for char in text).strip()


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
        # query = "snscrape --jsonl --max-results 1000 --since 2020-06-01 twitter-search 'TSLA until:2020-06-02'"
        # self.query = "snscrape --jsonl twitter-search 'from:JCOviedo6'"
        # self.query = "snscrape --jsonl --max-results 1000 twitter-search '1267031143636926465'"

    def get_likes(self, json):
        try:
            # Also convert to int since update_time will be string.  When comparing
            # strings, "10" is smaller than "2".
            return int(json['likeCount'])
        except KeyError:
            return 0

    def append_token(self, str):
        if (str == ""):
            return "{}"
        else:
            return str + "}"

    def call_snscrape(self, query):

        twitter_results = subprocess.check_output(
            query, shell=True).decode('utf-8')
        results_list = twitter_results.split('}\n')
        results_list = list(map(self.append_token, results_list))
        results_list.pop()
        extracted_json = list(
            map(lambda json_str: json.loads(json_str), results_list))

        for t in extracted_json:  # filter to get only english tweets
            if(t['lang'] != 'en'):
                extracted_json.remove(t)
            # if(detect(t['content']) != 'en'):
            #    extracted_json.remove(t)
        extracted_json.sort(key=self.get_likes, reverse=True)
        return extracted_json

    def scrape(self, date, stock):
        conversation_ids = []
        conversations = {}  # start building a dictionary of concatenated conversation objects, created from amalgamation of tweets
        date_start = date.strftime('%Y-%m-%d')
        date_end = (date+timedelta(days=1)).strftime('%Y-%m-%d')

        extracted_json = self.call_snscrape(
            "snscrape --jsonl --max-results 20 --since %s twitter-search '%s until:%s'" % (date_start, stock, date_end))

        for e in extracted_json:  # for every tweet
            if e['lang'] != 'en':  # if the main language isn't english, ignore this conversation. Not worth it to parse in vader
                extracted_json.remove(e)
                continue
            conversation = {}
            # print(e)
            conversation_id = e['conversationId']
            if conversation_id in conversation_ids:  # if this conversation has already been recorded, don't add a duplicate
                print("CONVERSATION ALREADY ADDED. SKIPPING...\n")
                continue

            conversation_ids.append(conversation_id)
            print('ADDING CONVERSATION %d FROM %s...\n' %
                  (conversation_id, e['url']))

            conversation_json = self.call_snscrape(  # conversation_json is ordered most recent last
                "snscrape --jsonl twitter-search 'conversation_id:%d filter:safe'" % (conversation_id))

            quoted_json = self.call_snscrape(
                "snscrape --jsonl twitter-search 'quoted_tweet_id:%d filter:safe'" % (conversation_id))

            for q in quoted_json:
                conversation_json.append(q)

            parent_json = []  # note: Sometimes parent tweets just dont exist???
            if e['inReplyToUser'] == None:
                parent_json.append(e)
            else:
                parent_json = self.call_snscrape(
                    "snscrape --jsonl twitter-search 'since_id:%d max_id:%d filter:safe'" % (conversation_id-1, conversation_id))

            if len(parent_json) != 0:
                conversation_json.append(parent_json[0])

            # append quoted tweet if parent is retweeting an old tweet
            if conversation_json[len(conversation_json)-1]['quotedTweet'] != None:
                conversation_json.append(
                    conversation_json[len(conversation_json)-1]['quotedTweet'])

            for tweet in conversation_json:  # for each tweet in conversation
                # space out emojis, remove new lines
                reply = {}
                content = add_space(tweet['content'])
                content = content.replace('\n', ' ')
                mentioned = []
                links = []
                cashtags = []
                hashtags = []
                if tweet['tcooutlinks'] != None:
                    links = tweet['tcooutlinks']
                if tweet['cashtags'] != None:
                    cashtags = tweet['cashtags']
                if tweet['hashtags'] != None:
                    hashtags = tweet['hashtags']
                if ('mentionedUsers' in tweet) and (tweet['mentionedUsers'] != None):
                    for m in tweet['mentionedUsers']:
                        mentioned.append(m['username'])

                links = set(links)
                cashtags = set(cashtags)
                hashtags = set(hashtags)
                mentioned = set(mentioned)

                redundant_links = [
                    l for l in content.split() if l.startswith('https://t.co/')]
                if redundant_links is not None:
                    for l in redundant_links:
                        content = content.replace(l, '')

                # print("%s: @%s | LIKES: %s | FOLLOWERS: %s | CASHTAGS: %s | HASHTAGS: %s | MENTIONED: %s | ORIGINAL: %s | LINKS: %s | \n %s\n" % (
                    # tweet['date'], tweet['user']['username'], tweet['likeCount'], tweet['user']['followersCount'], cashtags, hashtags, mentioned, tweet['url'], links, content))

                reply['username'] = tweet['user']['username']
                reply['followers'] = tweet['user']['followersCount']
                reply['likes'] = tweet['likeCount']
                reply['links'] = list(links)
                reply['mentioned'] = list(mentioned)
                reply['cashtags'] = list(cashtags)
                reply['hashtags'] = list(hashtags)
                reply['content'] = content
                conversation[tweet['date']] = reply
            if len(parent_json) != 0:
                conversation['url'] = parent_json[0]['url']
            else:
                conversation['url'] = conversation_json[len(
                    conversation_json)-1]['url']

            conversations[conversation_id] = conversation

        print("%d tweets analyzed, %d conversations" %
              (len(extracted_json), len(conversation_ids)))
        file_path = '../scraped_data/%s/twitter.json' % (date_start)
        Path("../scraped_data/%s/" % (date_start)
             ).mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w+') as f:
            json.dump(conversations, f)
            # threads = json.dumps(threads)


ts = TwitterScraper()
data = ts.scrape(datetime(2020, 6, 1), 'TSLA')
# print(data)

# 'followersCount': 5783, 'friendsCount': 993, 'statusesCount': 83163, 'favouritesCount': 200332, 'listedCount': 134, 'mediaCount': 2240,
