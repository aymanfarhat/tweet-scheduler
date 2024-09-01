"""Simple web server module built with fastapi"""
import os
from datetime import datetime
from dotenv import load_dotenv
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from google.cloud import firestore
import google.generativeai as genai
import tweepy

from models import Tweet, OptimizeRequest

logging.basicConfig(level=logging.ERROR)
load_dotenv()

db = firestore.Client(
    project=os.getenv("FIRESTORE_PROJECT_ID"),
    database=os.getenv("FIRESTORE_DATABASE_NAME"),
)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

@app.get("/")
def read_root(request: Request):
    """
    Renders and returns the content of the index.html file.

    Returns:
        str: The content of the index.html file.
    """
    return templates.TemplateResponse(
        request=request, name="index.html",
    )

@app.post("/api/tweets")
async def create_tweet(tweet: Tweet):
    """
    Creates a new tweet in the Firestore database.

    Args:
        tweet (Tweet): The tweet data.

    Returns:
        dict: The created tweet with its ID.
    """
    tweet_dict = tweet.dict()
    doc_ref = db.collection("tweets").document()
    doc_ref.set(tweet_dict)
    return {"id": doc_ref.id, **tweet_dict}
@app.get("/api/tweets")
async def get_tweets():
    """
    Retrieves all tweets from the Firestore database, ordered by publish time in descending order.

    Returns:
        list: A list of all tweets, sorted by publish time (newest first).
    """
    docs = db.collection("tweets").order_by("publish_time", direction=firestore.Query.DESCENDING).stream()
    return [{"id": doc.id, **doc.to_dict()} for doc in docs]

@app.delete("/api/tweets/{tweet_id}")
async def delete_tweet(tweet_id: str):
    """
    Deletes a tweet from the Firestore database.

    Args:
        tweet_id (str): The ID of the tweet to delete.

    Returns:
        dict: A success message.
    """
    db.collection("tweets").document(tweet_id).delete()
    return {"message": "Tweet deleted successfully"}

@app.put("/api/tweets/{tweet_id}/publish")
async def publish_tweet(tweet_id: str):
    """
    Publishes a tweet using the Twitter API and deletes it from the database.

    Args:
        tweet_id (str): The ID of the tweet to publish.

    Returns:
        dict: The published tweet information.
    """
    doc_ref = db.collection("tweets").document(tweet_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Tweet not found")

    tweet_data = doc.to_dict()

    try:
        client = tweepy.Client(
            consumer_key=os.getenv("X_CONSUMER_KEY"),
            consumer_secret=os.getenv("X_CONSUMER_SECRET"),
            access_token=os.getenv("X_ACCESS_TOKEN"),
            access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET")
        )
        client.create_tweet(text=tweet_data["content"])
        doc_ref.delete()
    except tweepy.errors.TweepyException as e:
        logging.error(f"Error publishing tweet: {e}")
    except Exception as e:
        logging.error(f"Error publishing tweet: {e}")

    return {"message": "Tweet published successfully"}

@app.post("/api/optimize")
async def optimize_text(request: OptimizeRequest):
    """
    Placeholder endpoint for optimizing text using an LLM.

    Args:
        request (OptimizeRequest): The request containing the text to optimize.
    Returns:
        dict: The original and optimized text.
    """
    original_text = request.text

    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(f"""
    You are a helpful assistant that optimizes text for a Twitter.
    You will be given a text and you need to optimize it for Twitter.
    Here are some guidelines:
    - The text should be concise and to the point.
    - The text should be engaging and persuasive.
    - The text should be relevant to the topic.
    - The text should be unique and not generic.
    - The text should be grammatically correct.
    - The text should be optimized for Twitter, max 280 characters.
    The text is: {original_text}
    """)
    optimized_text = response.text

    return {
        "original_text": original_text,
        "optimized_text": optimized_text
    }
