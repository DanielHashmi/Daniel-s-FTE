"""
Real Twitter Poster - Uses your actual API keys from .env
"""
import os
import tweepy
from dotenv import load_dotenv

load_dotenv()

def post_tweet(message: str) -> dict:
    """Post a real tweet to Twitter/X"""
    try:
        # Get credentials from .env
        client = tweepy.Client(
            consumer_key=os.getenv("TWITTER_API_KEY"),
            consumer_secret=os.getenv("TWITTER_API_SECRET"),
            access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
            access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        )
        
        # Post the tweet
        response = client.create_tweet(text=message)
        
        tweet_id = response.data['id']
        print(f"[SUCCESS] Tweet posted! ID: {tweet_id}")
        print(f"[URL] https://twitter.com/i/web/status/{tweet_id}")
        
        return {
            "success": True,
            "tweet_id": tweet_id,
            "url": f"https://twitter.com/i/web/status/{tweet_id}"
        }
        
    except Exception as e:
        print(f"[ERROR] Failed to post tweet: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        message = " ".join(sys.argv[1:])
    else:
        message = "Testing my AI Employee system! 🤖 #AIEmployee #Hackathon"
    
    print(f"Posting tweet: {message}")
    result = post_tweet(message)
    print(result)
