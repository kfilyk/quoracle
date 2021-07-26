from RedditScraper import RedditScraper
from TwitterScraper import TwitterScraper
import os
from os import path
import json

if __name__ == "__main__":
    from_reddit = RedditScraper().scrape()
    from_twitter = TwitterScraper().scrape()
    joined_results = from_reddit + from_twitter
    output_filename = "scrapers_output.txt"
    if (path.exists(output_filename)):
        os.remove(output_filename)
    with open(output_filename, "w") as f:
        f.write(json.dumps(joined_results))
        print(f"successfully wrote {len(joined_results)} articles to {output_filename}")