import os
import json
import subprocess
from Scraper import Scraper
from langdetect import detect
from datetime import datetime, timedelta
from pathlib import Path


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
        #query = "snscrape --jsonl --max-results 1000 --since 2020-06-01 twitter-search 'TSLA until:2020-06-02'"
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
        threads = {}  # start building a dictionary of concatenated conversation objects, created from amalgamation of tweets
        date_start = date.strftime('%Y-%m-%d')
        date_end = (date+timedelta(days=1)).strftime('%Y-%m-%d')

        extracted_json = self.call_snscrape(
            "snscrape --jsonl --max-results 1000 --since %s twitter-search '%s until:%s'" % (date_start, stock, date_end))

        i = 1
        for t in extracted_json:  # for every tweet

            # if('mentionedUsers' in t) and (t['mentionedUsers'] != None):
            # print("%s\n" % t)  # print each tweet
            thread = {}
            conversation = t['conversationId']
            if t['conversationId'] is not None:  # store conv
                thread['conversationId'] = t['conversationId']

            # each thread
            content = t['content']
            mentioned = []
            links = []
            cashtags = []
            hashtags = []
            if t['tcooutlinks'] != None:
                links = t['tcooutlinks']
            if t['cashtags'] != None:
                cashtags = t['cashtags']
            if t['hashtags'] != None:
                hashtags = t['hashtags']
            if ('mentionedUsers' in t) and (t['mentionedUsers'] != None):
                for m in t['mentionedUsers']:
                    mentioned.append(m['username'])

            q_ids = []
            q = t['quotedTweet']  # get chain of all previously quoted tweets
            while q is not None:  # get chain of all
                if q['id'] not in q_ids:  # continue as long as there isnt a loop
                    content = q['content'] + '\n' + content
                    if q['tcooutlinks'] is not None:
                        links.extend(q['tcooutlinks'])  # add to set
                    if q['cashtags'] is not None:
                        cashtags.extend(q['cashtags'])
                    if q['hashtags'] is not None:
                        hashtags.extend(q['hashtags'])
                    if ('mentionedUsers' in q) and (q['mentionedUsers'] != None):
                        for m in q['mentionedUsers']:
                            mentioned.append(m['username'])
                    q_ids.append(q['id'])
                    q = q['quotedTweet']
                else:
                    break
            """
            r_ids = []
            r = t['inReplyToTweetId']
            while r is not None:
                if r not in r_ids:
                    # if this tweet was a comment, find and append the original tweet
                    ptid = t['inReplyToTweetId']  # parent tweet id
                    print("TWEET ID:" + ptid)
                    print("CONVO ID: " + t['conversationId'])
                    print(t)
                    parent_tweet = self.call_snscrape(
                        "snscrape --jsonl twitter-search 'from:%s since_id:%d max_id:%d filter:safe'" % (t['inReplyToUser']['username'], ptid-1, ptid+1))
                    if len(parent_tweet) == 0:
                        from_date = '2006-03-22'
                        if t['inReplyToUser']['created'] is not None:
                            from_date = datetime.strptime(
                                t['inReplyToUser']['created'][:10], '%Y-%m-%d')
                        until_date = datetime.strptime(
                            t['date'][:10], '%Y-%m-%d')
                        print(from_date)
                        print(until_date)
                        until_date += datetime.timedelta(days=1)
                        # get list of all tweets from the conversation parent profile
                        parent_tweet = self.call_snscrape(
                            "snscrape --jsonl twitter-search --since %s 'from:%s until:%s'" % (from_date, t['inReplyToUser']['username'], until_date))
                        for pt in parent_tweet:
                            # if this is actually the conversation
                            if pt['conversationId'] != t['conversationId']:
                                if pt['id'] != t['inReplyToTweetId']:
                                    parent_tweet.remove(pt)
                        print(len(parent_tweet))
                    if parent_tweet['content'] is not None:
                        content = parent_tweet['content'] + '\n' + content
                    if parent_tweet['tcooutlinks'] is not None:
                        links.extend(parent_tweet['tcooutlinks'])  # add to set
                    if parent_tweet['cashtags'] is not None:
                        cashtags.extend(parent_tweet['cashtags'])
                    if parent_tweet['hashtags'] is not None:
                        hashtags.extend(parent_tweet['hashtags'])
                    if ('mentionedUsers' in parent_tweet) and (parent_tweet['mentionedUsers'] != None):
                        for m in parent_tweet['mentionedUsers']:
                            mentioned.append(m['username'])

                    r_ids.append(r['id'])
                    print(parent_tweet)

                    r = r['parentTweet']
                else:
                    break
                """

            links = set(links)
            cashtags = set(cashtags)
            hashtags = set(hashtags)
            mentioned = set(mentioned)
            if cashtags is not None:
                for c in cashtags:
                    content = content.replace('$'+c, c)
            if hashtags is not None:
                for h in hashtags:
                    content = content.replace('#'+h, h)
            if links is not None:
                for l in links:
                    content = content.replace(l, '')
            if mentioned is not None:
                for m in mentioned:
                    content = content.replace('@'+m, '')
            content = content.replace('\n', ' ')
            redundant_links = [
                t for t in content.split() if t.startswith('https://t.co/')]
            if redundant_links is not None:
                for l in redundant_links:
                    content = content.replace(l, '')

            print("%d. %s | LIKES: %s | FOLLOWERS: %s | CASHTAGS: %s | HASHTAGS: %s | MENTIONED: %s | ORIGINAL: %s | LINKS: %s | \n %s\n" % (
                i, t['user']['username'], t['likeCount'], t['user']['followersCount'], cashtags, hashtags, mentioned, t['url'], links, content))
            i = i+1
            thread['content'] = content
            threads[t['conversationId']] = thread

        print("(%d TWEETS)" % (i-1))
        file_path = '../scraped_data/%s/twitter.json' % (date_start)
        Path("../scraped_data/%s/" % (date_start)
             ).mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w+') as f:
            json.dump(threads, f)
            #threads = json.dumps(threads)


ts = TwitterScraper()
data = ts.scrape(datetime(2020, 6, 1), 'TSLA')
# print(data)

# 'followersCount': 5783, 'friendsCount': 993, 'statusesCount': 83163, 'favouritesCount': 200332, 'listedCount': 134, 'mediaCount': 2240,
