
import emoji
from pathlib import Path
from datetime import datetime, timedelta
from Scraper import Scraper
import re
import subprocess
import json
import os
import math


def extract_emojis(s):
    return ''.join(c for c in s if c in emoji.UNICODE_EMOJI['en'])


def space_emojis(text):
    emojis = extract_emojis(text)
    for e in emojis:  # go through every emoji
        text = text.replace(e, ' e_'+emoji.demojize(e, delimiters=("", " ")))
    return text


def append_token(str):
    if (str == ""):
        return "{}"
    else:
        return str + "}"


def get_likes(json):
    try:
        # Also convert to int since update_time will be string.  When comparing
        # strings, "10" is smaller than "2".
        return int(json['likeCount'])
    except KeyError:
        return 0


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

    def call_snscrape(self, query):
        twitter_results = subprocess.check_output(
            query, shell=True).decode('utf-8')  # need shell=True
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

    def scrape(self, date, stock):
        # Note: tweet_urls is useful for restarting TweetExtraction after an error has occured. will not overwrite previously written json- simply adds to it.
        convos = {}
        tweet_urls = []
        date_start = date.strftime('%Y-%m-%d')
        date_end = (date+timedelta(days=1)).strftime('%Y-%m-%d')

        file_path = '../data/raw/%s/%s/twitter.json' % (date_start, stock)
        Path("../data/raw/%s/%s" % (date_start, stock)
             ).mkdir(parents=True, exist_ok=True)

        # "snscrape --jsonl --max-results 20 --since %s twitter-search '%s until:%s'" % (date_start, stock, date_end))
        extracted_json = self.call_snscrape(
            "snscrape --jsonl --since %s twitter-search '%s until:%s'" % (date_start, stock, date_end))

        num_extracted = len(extracted_json)
        print(num_extracted)
        # finds every conversation thread from results of snscrape
        for ext_idx, tweet in enumerate(extracted_json):
            # if this conversation has already been recorded, don't add a duplicate
            if tweet['url'] in tweet_urls:
                print("%d/%d. TWEET ALREADY ADDED. SKIPPING..." %
                      (ext_idx, num_extracted))
                continue

            if tweet['lang'] != 'en':  # if the main language isn't english, ignore this conversation
                print("%d/%d. TWEET NOT IN ENGLISH. SKIPPING..." %
                      (ext_idx, num_extracted))
                continue

            tweet_urls.append(tweet['url'])  # adding tweet

            tweet_json = {}
            content = tweet['content']  # space out emojis
            # print(content)
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

            # get rid of non-unique elements in each; sort from longest str len to shortest for ease of replacement
            links = sorted(list(set(links)), key=len, reverse=True)
            cashtags = sorted(list(set(cashtags)), key=len, reverse=True)
            hashtags = sorted(list(set(hashtags)), key=len, reverse=True)
            mentioned = sorted(list(set(mentioned)), key=len, reverse=True)
            redundant_links = [
                l for l in content.split() if l.startswith('https://t.co/')]
            if redundant_links is not None:
                for l in redundant_links:
                    content = content.replace(l, '')

            # insert tweeter name, round(log10(tweet likes)), at start of tweet
            log_likes = 'log_likes_'
            log_likes += str(round(2 *
                                   math.log10(int(tweet['likeCount'])+1)))
            # print(log_likes)

            log_followers = 'log_followers_' + str(round(2 *
                                                         math.log10(int(tweet['user']['followersCount'])+1)))

            log_activity = 'log_activity_' + str(round(2 *
                                                       math.log10(tweet['quoteCount']+tweet['retweetCount']+tweet['replyCount']+1)))

            content = '@'+tweet['user']['username'] + \
                ' ' + log_likes + ' ' + log_followers + ' ' + log_activity + ' ' + content

            content = content.replace('\u00a0', '')
            content = content.replace('\ud83c', '')
            content = content.replace('\u2014', ' ')
            content = content.replace('\u2014', ' ')
            content = content.replace('\u2066', ' ')
            content = content.replace('\u2069', ' ')
            content = content.replace('\\u', ' \\u')
            content = space_emojis(
                content)  # space out emojis

            content = content.replace('\n', ' ')
            content = content.replace('dollars', ' $ ')
            content = content.replace('dollar', ' $ ')
            content = content.replace('plus', ' + ')

            content = content.replace('\u00a3', ' $ ')

            content = content.replace('\u201c', '\'')
            content = content.replace('\u201d', '\'')
            content = content.replace('\ufe0f', '')
            content = content.replace('&gt;', '> ')
            content = content.replace('&lt;', ' <')
            content = content.replace('\"', ' \' ')
            content = content.replace('‘', '\'')
            content = content.replace('’', '\'')
            content = content.replace('`', '\'')
            content = content.replace('/', ' ')
            content = content.replace('%', ' % ')
            content = content.replace('percentage', ' % ')
            content = content.replace('percent', ' % ')
            content = content.lower()  # convert to lower case

            content = re.sub(r"won\'t", "will not", content)
            content = re.sub(r"can\'t", "can not", content)
            content = re.sub(r"let\'s", "let us", content)

            # general
            content = re.sub(r"n\'t", " not", content)
            content = re.sub(r"\'re", " are", content)
            content = re.sub(r"\'s", " is", content)
            content = re.sub(r"\'d", " would", content)
            content = re.sub(r"\'ll", " will", content)
            content = re.sub(r"\'t", " not", content)
            content = re.sub(r"\'ve", " have", content)
            content = re.sub(r"\'m", " am", content)
            content = re.sub(r'[.][.][.]*', ' ellipses ', content)

            content = content.replace('H&amp;H', 'H&H')
            content = content.replace('J&amp;J', 'J&J')
            content = content.replace('S&amp;P', 'S&P')
            content = content.replace('R&amp;D', 'R&D')
            content = content.replace(' &amp; ', ' and ')
            # Use regex to replace any number > 2 of periods with a single ellipses: ........, .., ......., ... .., ..  -> ...

            # content = re.sub(r'^[0-9]*[.,]{0,1}[0-9]*$', "will not", content)  # note: build regex to replace numbers with log scaled approximate

            if cashtags is not None:
                for c in cashtags:
                    # hashtags/cashtags require spaces in between; this ensures proper collection
                    # content = content.replace('$'+c, c.upper())
                    content = content.replace(
                        '$'+c.lower(), ' ' + c.lower() + ' ')
                    #cashtags[i] = c.upper()

            if hashtags is not None:
                for h in hashtags:
                    # content = content.replace('#'+h, h.upper()+' ')
                    content = content.replace(
                        '#'+h.lower(), ' ' + h.lower() + ' ')
                    #hashtags[i] = h.upper()

            if mentioned is not None:
                for i, m in enumerate(mentioned):
                    ml = m.lower()
                    content = content.replace('@'+ml, ' @'+m+' ')

            content = re.sub('([.,!?()\'-*$+=:])', r' \1 ', content)

            # print("%s: @%s | LIKES: %s | FOLLOWERS: %s | CASHTAGS: %s | HASHTAGS: %s | MENTIONED: %s | ORIGINAL: %s | LINKS: %s | \n %s\n" % (
            #    tweet['date'], tweet['user']['username'], tweet['likeCount'], tweet['user']['followersCount'], cashtags, hashtags, mentioned, tweet['url'], links, content))

            #tweet_json['oc'] = tweet['content']
            convos[tweet['url']] = content
        with open(file_path, 'w+') as f:
            json.dump(convos, f)

        print("%d tweets analyzed, %d recorded" %
              (num_extracted, len(tweet_urls)))


if __name__ == '__main__':
    ts = TwitterScraper()
    data = ts.scrape(datetime(2021, 3, 1), 'TSLA')
