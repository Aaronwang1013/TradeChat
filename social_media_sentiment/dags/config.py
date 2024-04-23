from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    MONGODB_USER: str = os.getenv("MONGODB_USER")
    MONGODB_PASSWORD: str = os.getenv("MONGODB_PASSWORD")
    REDDIT_CLIENT_ID: str = os.getenv("REDDIT_CLIENT_ID")
    REDDIT_CLIENT_SECRET: str = os.getenv("REDDIT_CLIENT_SECRET")
    REDDIT_USER_NAME: str = os.getenv("REDDIT_USER_NAME")
    REDDIT_PASSWORD: str = os.getenv("REDDIT_PASSWORD")
    REDDIT_USER_AGENT: str = os.getenv("REDDIT_USER_AGENT")