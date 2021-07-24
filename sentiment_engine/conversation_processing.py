import nltk
import json

def encode(tweet):
    words = nltk.word_tokenize(tweet)
    encoded_tweet = []
    for word in words:
        if (encoding_dict.get(word)):
            encoded_tweet.append(word)
        
    return encoded_tweet

def encode_conversation(file_path):
    conversations = []
    with open(file_path) as f:
        for jsonObj in f:
            conv_json = f.read()
            conversations.append(json.loads(jsonObj))
    for conversation in conversations:
        tweets = [conversation[key]['content'] for key in conversation.keys() if key != 'url' and key != 'conversation_id']
        encoded_conversation = [encode(tweet) for tweet in tweets]
    return encoded_conversation

if __name__ == "__main__":
    print(encode_conversation("twitter.json"))