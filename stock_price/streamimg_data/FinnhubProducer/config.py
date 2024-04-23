from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    FINN_API_KEY: str = os.getenv("FINN_API_KEY")
    KAFKA_SERVER: str = os.getenv("KAFKA_SERVER")
    KAFKA_PORT: str = os.getenv("KAFKA_PORT")
    KAFKA_TOPIC: str = os.getenv("KAFKA_TOPIC")