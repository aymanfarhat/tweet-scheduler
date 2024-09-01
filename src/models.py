from datetime import datetime
from pydantic import BaseModel

class Tweet(BaseModel):
    """
    Represents a tweet object.
    """
    content: str
    publish_time: datetime

class OptimizeRequest(BaseModel):
    """
    Represents the request body for tweet optimization.
    """
    text: str