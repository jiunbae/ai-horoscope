#!/usr/bin/env python3
"""Post horoscope tweet to X (Twitter) using Tweepy."""

import json
import os
import tweepy
from pathlib import Path


def post():
    data_path = Path(__file__).resolve().parent.parent / "data" / "latest.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    tweet_text = data["full_tweet"]

    # Add site link
    site_url = "https://jiunbae.github.io/ai-horoscope/"
    tweet_text += f"\n\n\U0001f517 {site_url}"

    # Check credentials
    required_env = [
        "TWITTER_API_KEY",
        "TWITTER_API_SECRET",
        "TWITTER_ACCESS_TOKEN",
        "TWITTER_ACCESS_TOKEN_SECRET",
    ]
    missing = [k for k in required_env if not os.environ.get(k)]
    if missing:
        print(f"Missing environment variables: {', '.join(missing)}")
        print("Skipping tweet posting.")
        return

    client = tweepy.Client(
        consumer_key=os.environ["TWITTER_API_KEY"],
        consumer_secret=os.environ["TWITTER_API_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_TOKEN_SECRET"],
    )

    response = client.create_tweet(text=tweet_text)
    print(f"Tweet posted: {response.data['id']}")
    print(f"Tweet text:\n{tweet_text}")


if __name__ == "__main__":
    post()
