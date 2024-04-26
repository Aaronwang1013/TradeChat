from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API")
