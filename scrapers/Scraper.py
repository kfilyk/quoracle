import json

class Scraper:
    mapper_dict = {
        "content": lambda: None,
        "source": lambda: None,
        "author": lambda: None
    }
    def extract_data(self, raw_json_list):
        data_list = list(map(lambda json_str: json.loads(json_str), raw_json_list))
        return list(map(lambda payload: {
                    "content": self.mapper_dict.get("content")(payload),
                    "source": self.mapper_dict.get("source")(payload),
                    "author": self.mapper_dict.get("author")(payload)
                },
                data_list
            )
        )