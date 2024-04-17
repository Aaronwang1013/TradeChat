from dotenv import load_dotenv
import os

load_dotenv()




class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    MONGODB_USER: str = os.getenv("MONGODB_USER")
    MONGODB_PASSWORD: str = os.getenv("MONGODB_PASSWORD")
    