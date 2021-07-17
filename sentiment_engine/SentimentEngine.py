import json
import os
import re
from abc import ABC
import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')

class Particle:
    def __init__(self, message, start_index = 0):
        self.content = message
        self.center_index = start_index + (len(message) // 2)
    def __str__(self):
        return str({
            "content": self.content,
            "center_index": self.center_index
        })

class ProcessedMessage:
    def __init__(self, raw_content, num_words_per_particle = 5):
        self.stop_words = set(stopwords.words('english'))
        self.tickers = []
        #ticker_regex = re.compile("(\$|\@)([A-Za-z]*)")
        ticker_regex = re.compile("( ||)(\$)([A-Z]*)( ||)")
        ticker_index_diffs = []
        content = raw_content
        prev_ticker_symbol_length = 0
        for ticker in ticker_regex.finditer(content):
            symbol = ticker.group().strip()
            ticker_index = ticker.start() - prev_ticker_symbol_length
            prev_ticker_symbol_length += len(symbol)
            self.tickers.append({"symbol": symbol, "index": ticker_index})
            content = content.replace(symbol, '')
        self.content = content.strip()
        self.num_words_per_particle = num_words_per_particle
        self.particles = []
    def particlize(self):
        n = self.num_words_per_particle
        words = self.content.split(" ")
        particles = []
        particle_i = 0
        char_index = 0
        particle_start_index = 0
        for word in words:
            if (len(word) > 0 and not word.lower() in self.stop_words):
                particles.append(Particle(word, particle_start_index))
            particle_i += 1
            particle_start_index = char_index
            char_index += len(word) + 1 # extra 1 for the appended space after each word
        self.particles = particles
    def __str__(self):
        return str({
            "tickers": self.tickers,
            "content": self.content,
            "particles": [str(particle) for particle in self.particles]
        })
    def print_particles(self):
        print([str(particle) for particle in self.particles])

def squared_distance(point_1, point_2):
    return ((point_1) - (point_2))**2

def associate_particles_with_tickers(processed_message):
    result = {}
    for ticker in processed_message.tickers:
        if (result.get(ticker['symbol']) == None):
            result[ticker['symbol']] = []
        for particle in processed_message.particles:
            result[ticker['symbol']].append({'particle': particle.content, 'distance': squared_distance(ticker['index'], particle.center_index)})
    return result

if __name__ == "__main__":
    message = 'expecting $TSLA to slide, but coupling to $BTC may change the game. $BTC $GME $AMC'
    processed_message = ProcessedMessage(message)
    processed_message.particlize()
    result = associate_particles_with_tickers(processed_message)
    print(result)