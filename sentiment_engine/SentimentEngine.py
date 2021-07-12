from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import json
import os
import re

class Sentiment:
    def __init__(self, ticker, neg = 0, neu = 0, pos = 0):
        self.ticker = ticker
        self.neg = neg
        self.neu = neu
        self.pos = pos
    def __add__(self, other):
        if (self.ticker != other.ticker):
            raise Exception(f"Error: tickers in sentiment object do not match: {self.ticker}, {other.ticker}")
        self.neg += other.neg
        self.neu += other.neu
        self.pos += other.pos
        return self
    def __truediv__(self, other):
        if (self.ticker != other.ticker):
            raise Exception(f"Error: tickers in sentiment object do not match: {self.ticker}, {other.ticker}")
        self.neg = self.neg / other.neg
        self.neu = self.neu / other.neu
        self.pos = self.pos / other.pos
        return self
    def __str__(self):
        return str({
            "ticker": self.ticker,
            "neg": self.neg,
            "neu": self.neu,
            "pos": self.pos
        })

class SentimentEngine:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        POSITIVE = " positive"
        NEGATIVE = " negative"
        with open(os.getcwd() + "/sentiment_engine/KnownSlang.json", "r") as f:
            known_slang = f.read()
            self.slang_interpreter = json.loads(known_slang)
        self.scores = []

    def replace_slang(self, original_message):
        slang_terms = list(self.slang_interpreter.keys())
        result = original_message
        for term in slang_terms:
            interpretation = self.slang_interpreter[term]
            caseInsensitiveTerm = re.compile(re.escape(term), re.IGNORECASE)
            result = caseInsensitiveTerm.sub(f"{interpretation} ", result)
        return result

    def analyze_processed_message(self, processed_message):
        segments = processed_message.parse_segments()
        tickers = processed_message.tickers
        for segment in segments:
            self.analyze(segment.ticker, segment.content)
        return self

    def analyze(self, ticker, message):
        score = self.analyzer.polarity_scores(self.replace_slang(message))
        self.scores.append(Sentiment(ticker, score["neg"], score["neu"], score["pos"]))
        return self

    def accumulate_scores(self):
        scores = self.scores
        result = Sentiment()
        for score in scores:
            result = result + score
        self.scores = [result]
        return self
    
    def average_scores(self):
        number_of_scores = len(self.scores)
        self.accumulate_scores()
        self.scores = [self.scores[0] / Sentiment(number_of_scores, number_of_scores, number_of_scores)]
        return self

    def get(self):
        return self.scores

    def print_scores(self):
        print([str(score) for score in self.scores])

class Segment:
    def __init__(self, ticker, message):
        self.ticker = ticker
        self.content = message

class ProcessedMessage:
    def __init__(self, raw_content):
        self.tickers = []
        ticker_regex = re.compile("\$([A-Z]*)")
        for ticker in ticker_regex.finditer(raw_content):
            self.tickers.append({"symbol": ticker.group(), "index": ticker.start()})
        self.content = ticker_regex.sub('', raw_content)
    def parse_segments(self):
        split_message = self.content.split(',')
        segments = []
        for ticker_i in range(len(self.tickers)):
            ticker = self.tickers[ticker_i]
            message = split_message[ticker_i]
            segments.append(Segment(ticker, message))
        return segments
    def __str__(self):
        return str({"tickers": self.tickers, "content": self.content})
        
if __name__ == "__main__":
    message = '$TSLA GOING UP, $BTC UP, $GME TO THE MOON, $ENEMYSTOCK GOING DOWN, $BNX GOING UP, $NIO GOING UP, $BIGOIL GOING DOWN'
    processed_message = ProcessedMessage(message)
    sentiment_engine = SentimentEngine()
    sentiment_engine.analyze_processed_message(processed_message)
    sentiment_engine.print_scores()