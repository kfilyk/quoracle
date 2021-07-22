
import emoji
from pathlib import Path
from datetime import datetime, timedelta
from Scraper import Scraper
import string
import re
import subprocess
import json
import os
import math
import multiprocessing


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


def call_snscrape_async(query, dict):
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
    dict['conversation_json'] = extracted_json


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
        conversation_ids = []
        date_start = date.strftime('%Y-%m-%d')
        date_end = (date+timedelta(days=1)).strftime('%Y-%m-%d')

        file_path = '../scraped_data/%s/%s/twitter.json' % (date_start, stock)
        Path("../scraped_data/%s/%s" % (date_start, stock)
             ).mkdir(parents=True, exist_ok=True)
        if os.path.isfile(file_path):
            with open(file_path) as f:
                for jsonObj in f:
                    j = json.loads(jsonObj)
                    # append every conversation id that already exists
                    conversation_ids.append(j['conversation_id'])
        else:
            open(file_path, 'w+')

        # "snscrape --jsonl --max-results 20 --since %s twitter-search '%s until:%s'" % (date_start, stock, date_end))
        extracted_json = self.call_snscrape("snscrape --jsonl --since %s twitter-search '%s until:%s'" % (date_start, '$'+stock, date_end)) + \
            self.call_snscrape("snscrape --jsonl --since %s twitter-search '%s until:%s'" %
                               (date_start, '#'+stock, date_end))
        num_extracted = len(extracted_json)
        print(num_extracted)
        # finds every conversation thread from results of snscrape
        for ext_idx, e in enumerate(extracted_json):
            # if this conversation has already been recorded, don't add a duplicate
            conversation_id = e['conversationId']
            if conversation_id in conversation_ids:
                print("%d/%d. CONVERSATION ALREADY ADDED. SKIPPING...\n" %
                      (ext_idx, num_extracted))
                continue

            if e['lang'] != 'en':  # if the main language isn't english, ignore this conversation
                print("%d/%d. TWEET NOT IN ENGLISH. SKIPPING...\n" %
                      (ext_idx, num_extracted))
                continue

            # print(e['content'].replace('\n', '')+'\n\n\n')
            if '#'+stock not in e['content'] and '$'+stock not in e['content']:
                print("%d/%d. TWEET DOES NOT MENTION STOCK. SKIPPING...\n" %
                      (ext_idx, num_extracted))
                # comment doesn't have anything to do with stock - continue
                continue

            conversation = {}
            d = mp_manager.dict()
            conversation_ids.append(conversation_id)
            print("%d/%d. TRYING CONVERSATION %d..." %
                  (ext_idx, num_extracted, conversation_id))

            # get the entire conversation associated with this conversation_id. conversation_json is ordered most recent last
            p = multiprocessing.Process(target=call_snscrape_async, args=(
                ("snscrape --jsonl twitter-search 'conversation_id:%d filter:safe'" % (conversation_id)), d))
            p.start()
            p.join(60)
            if p.is_alive():
                p.terminate()
                # OR Kill - will work for sure, no chance for process to finish nicely however
                # p.kill()
                print("... OK, TRYING AGAIN ...")
                p = multiprocessing.Process(target=call_snscrape_async, args=(
                    ("snscrape --jsonl twitter-search 'conversation_id:%d -filter:safe'" % (conversation_id)), d))
                p.start()
                p.join(120)
                if p.is_alive():  # still didn't resolve it
                    p.terminate()
                    print("FAILED! MOVING ON.")
                    continue  # just ignore this conversation then... its too big or st
            conversation_json = d['conversation_json']
            # conversation_json = self.call_snscrape(
            #    "snscrape --jsonl twitter-search 'conversation_id:%d filter:safe'" % (conversation_id))

            # note: Sometimes, parent tweet just doesnt exist.
            parent_json = []
            # this handles an edge case where 'conversation_json' does not include the parent of the conversation if e is the parent
            if e['inReplyToUser'] == None:
                parent_json.append(e)
            else:
                parent_json = self.call_snscrape(
                    "snscrape --jsonl twitter-search 'since_id:%d max_id:%d filter:safe'" % (conversation_id-1, conversation_id))

            if len(parent_json) != 0:  # if parent_json list is not empty (has 1 parent)
                # if the parent of the conversation is not yet included in the conversation_json list
                # print(len(conversation_json))
                # print(conversation_json[len(conversation_json)-1])
                if len(conversation_json) == 0:
                    conversation_json.append(
                        parent_json[0])  # append the parent
                elif conversation_json[len(conversation_json)-1]['id'] != conversation_id:
                    conversation_json.append(
                        parent_json[0])  # append the parent
                conversation['url'] = parent_json[0]['url']
            else:
                conversation['url'] = conversation_json[len(
                    conversation_json)-1]['url']
            print('...ADDED %s.\n' % conversation['url'])

            # insert quoted tweets from all tweets in conversation. Don't do this directly in a loop- len of json subject to change
            i = 0
            l = len(conversation_json)
            while i < l:
                tweet = conversation_json[i]
                if tweet['quotedTweet'] is not None:
                    # append all quoted tweets
                    conversation_json.insert(i+1, tweet['quotedTweet'])
                    i = i+2
                    l = len(conversation_json)
                else:
                    i = i+1

            # for each tweet in conversation
            for tweet in conversation_json:
                # print(tweet)
                # print('\n')
                reply = {}

                content = space_emojis(
                    tweet['content'])  # space out emojis

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
                content = '@'+tweet['user']['username'] + \
                    ' ' + log_likes + ' ' + content

                # insert number of likes on logarithmic scale? same with followers, retweets, etc?

                content = content.replace('\n', ' ')
                content = content.replace('&amp;', '&')
                content = content.replace('\'s', '')
                content = content.replace('‘s', '')
                content = content.replace('\'', '')
                content = content.replace('‘', '')
                content = content.replace('’', '')
                content = content.replace('`', '')
                content = re.sub('([.,!?()"-])', r' \1 ', content)
                content = content.replace('/', ' ')
                content = content.replace('/', ' ')
                content = content.lower()  # convert to lower case

                if cashtags is not None:
                    for i, c in enumerate(cashtags):
                        c = c.lower()
                        # hashtags/cashtags require spaces in between; this ensures proper collection
                        content = content.replace('$'+c+' ', c.upper()+' ')
                        cashtags[i] = c.upper()

                if hashtags is not None:
                    for i, h in enumerate(hashtags):
                        h = h.lower()
                        content = content.replace('#'+h+' ', h.upper()+' ')
                        hashtags[i] = h.upper()

                if mentioned is not None:
                    for i, m in enumerate(mentioned):
                        ml = m.lower()
                        content = content.replace('@'+ml, ' @'+m+' ')

                # print("%s: @%s | LIKES: %s | FOLLOWERS: %s | CASHTAGS: %s | HASHTAGS: %s | MENTIONED: %s | ORIGINAL: %s | LINKS: %s | \n %s\n" % (
                #    tweet['date'], tweet['user']['username'], tweet['likeCount'], tweet['user']['followersCount'], cashtags, hashtags, mentioned, tweet['url'], links, content))

                reply['username'] = tweet['user']['username']
                reply['followers'] = tweet['user']['followersCount']
                reply['likes'] = tweet['likeCount']
                # reply['links'] = links # ignore including links for now
                # reply['mentioned'] = mentioned
                reply['cashtags'] = cashtags
                reply['hashtags'] = hashtags
                reply['content'] = content
                conversation[tweet['date']] = reply

            conversation['conversation_id'] = conversation_id
            with open(file_path, 'a') as f:
                json.dump(conversation, f)
                f.write('\n')

        print("%d tweets analyzed, %d conversations" %
              (num_extracted, len(conversation_ids)))


if __name__ == '__main__':
    mp_manager = multiprocessing.Manager()
    ts = TwitterScraper()
    data = ts.scrape(datetime(2020, 3, 13), 'TSLA')

# print(data)

# 'followersCount': 5783, 'friendsCount': 993, 'statusesCount': 83163, 'favouritesCount': 200332, 'listedCount': 134, 'mediaCount': 2240,
