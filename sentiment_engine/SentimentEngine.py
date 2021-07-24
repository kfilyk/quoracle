import json
import os
import re
from abc import ABC
import nltk
from nltk.corpus import stopwords
import flair

nltk.download("punkt")
nltk.download('stopwords')

class Particle:
    def __init__(self, message, start_index = 0):
        self.content = message
        self.index = start_index
    def __str__(self):
        return str({
            "content": self.content,
            "index": self.index
        })

class ProcessedMessage:
    def __init__(self, raw_content, exclude_stop_words=True):
        self.tickers_set = set()
        self.tickers = []
        #ticker_regex = re.compile("(\$|\@)([A-Za-z]*)")
        ticker_regex = re.compile("( ||)(\$)([A-Z]*)( ||)")
        if (exclude_stop_words):
            stop_words = set(stopwords.words('english'))
        else:
            stop_words = set()
        content = raw_content
        words = [word for word in nltk.word_tokenize(content) if word.isalnum() or word == "$"]
        particles = []
        # header tickers should be assigned index of -1 to have 0 squared distance assigned for all particles
        index = 0
        while (index < len(words)):
            word = words[index]
            if (word == "$"):
                symbol = words[index + 1]
                self.tickers.append({"symbol": symbol, "index": -1})
                self.tickers_set.add(symbol)
                # delete cash tag
                del words[index]
                # delete ticker symbol associated with cash tag
                del words[index]
                index -= 1
            else:
                break
            index += 1
        # footer tickers should be assigned index of -1 to have 0 squared distance assigned for all particles
        index = len(words) - 2
        while (index >= 0):
            word = words[index]
            if (word == "$"):
                symbol = words[index + 1]
                self.tickers.append({"symbol": symbol, "index": -1})
                self.tickers_set.add(symbol)
                # delete cash tag
                del words[index]
                # delete ticker symbol associated with cash tag
                del words[index]
            else:
                break
            index -= 2
        # process tickers in content body
        index = 0
        while (index < len(words)):
            word = words[index]
            if (len(word) > 0 and (not word.lower() in stop_words) and not ticker_regex.match(word)):
                particle = Particle(word, index)
                particles.append(particle)
                index += 1
                continue
            elif (word == "$"):
                symbol = words[index + 1]
                self.tickers.append({"symbol": symbol, "index": index})
                self.tickers_set.add(symbol)
            index += 1

        self.particles = particles
        self.content = content.strip()
        self.particles = particles
        self.stop_words = stop_words

    def __str__(self):
        return str({
            "tickers": self.tickers,
            "content": self.content,
            "particles": [str(particle) for particle in self.particles]
        })
    def print_particles(self):
        print([str(particle) for particle in self.particles])

def squared_distance(point_1, point_2):
    if (point_1 < 0 or point_2 < 0):
        return 0
    return ((point_1) - (point_2))**2

def associate_particles_with_tickers(processed_message):
    result = {}
    for ticker in processed_message.tickers:
        symbol = ticker['symbol']
        if (result.get(symbol) == None):
            result[symbol] = {}
        for particle in processed_message.particles:
            if (not particle.content in processed_message.tickers_set):
                result[symbol][particle.content] = {
                    'squared_distance': squared_distance(ticker['index'], particle.index)
                }
    return result

class SentimentAnalyzer:
    def __init__(self):
        self.model = flair.models.TextClassifier.load('en-sentiment')
    def analyze(self, content):
        sample = flair.data.Sentence(content)
        self.model.predict(sample)
        label = sample.labels[0]
        positive_score = 0
        negative_score = 0
        if (label.value == 'POSITIVE'):
          positive_score = label.score
        elif (label.value == 'NEGATIVE'):
          negative_score = label.score
        result = {
            'pos': positive_score,
            'neg': negative_score
        }
        return result

if __name__ == "__main__":
    message = '$AMZN $AAPL expecting $TSLA to slide, but coupling to $BTC may change the game.  $GME $AMC $BTC '
    processed_message = ProcessedMessage(message, False)
    result = associate_particles_with_tickers(processed_message)
    print(result)
    sentiment = SentimentAnalyzer().analyze(message)