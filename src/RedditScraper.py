import os
import json
import subprocess
from Scraper import Scraper

class RedditScraper(Scraper):
    def __init__(self):
        self.mapper_dict = {
            "content": lambda payload: payload.get("selftext"),
            "source": lambda payload: "reddit",
            "author": lambda payload: payload.get("author")
        }
        self.query = "snscrape --jsonl --max-results 100 reddit-search 'DeepFuckingValue'"
    def _append_token(self, input_str):
        if (input_str == ""):
            return "{}"
        else:
            return input_str + "}"

    def scrape(self):
        reddit_results = subprocess.check_output(self.query, shell=True).decode('utf-8')
        results_list = reddit_results.split('}\n')
        results_list = list(map(self._append_token, results_list))
        extracted_content = self.extract_data(results_list)
        discarded_data = extracted_content.pop()
        return extracted_content