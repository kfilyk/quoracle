from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import json
import os

class Sentiment:
    def __init__(self, neg = 0, neu = 0, pos = 0):
        self.neg = neg
        self.neu = neu
        self.pos = pos
    def __add__(self, other):
        self.neg += other.neg
        self.neu += other.neu
        self.pos += other.pos
        return self
    def __str__(self):
        return str({
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
            result = result.replace(term.upper(), interpretation.upper()).replace(term.lower(), interpretation.lower())
        return result

    def analyze(self, message):
        score = self.analyzer.polarity_scores(self.replace_slang(message))
        self.scores.append(Sentiment(score["neg"], score["neu"], score["pos"]))
        return self

    def accumulate_scores(self):
        scores = self.scores
        result = Sentiment()
        for score in scores:
            result = result + score
        self.scores = [result]
        return self
    
    def get(self):
        return self.scores

    def print_scores(self):
        print([str(score) for score in self.scores])

if __name__ == "__main__":
    message = "tesla stocks to the moon!!"
    message2 = "tesla stocks to the moon!!"
    sentiment_engine = SentimentEngine()
    sentiment_engine.analyze(message).analyze(message).accumulate_scores().print_scores()