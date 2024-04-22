import json
import websocket
from src.utils.functions import *
from src.utils.functions import avro_encode
from config import Config
import time as ti
import logging


## set up logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)



class FinnhubProducer:

    def __init__(self) -> None:
        self.finnhub_client = load_client(Config.FINN_API_KEY)
        self.producer = load_producer(f"{Config.KAFKA_SERVER}:{Config.KAFKA_PORT}")
        self.avro_schema = load_avro_schema('src/schema/trades.avsc')
        # self.tickers = ["BINANCE:BTCUSDT", "TSLA", "NVDA", "AAPL", "AMZN", "GOOGL", "MSFT", "META"]
        self.tickers = ["BINANCE:BTCUSDT", "BINANCE:ETHUSDT"]
        ## get real-time stock data from finnhub
        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(f"wss://ws.finnhub.io?token={Config.FINN_API_KEY}",
                                         on_message= self.on_message,
                                         on_error= self.on_error,
                                         on_close= self.on_close)
        self.ws.on_open = self.on_open
        self.ws.run_forever()

    def on_message(self, ws, message):
        message = json.loads(message)
        try:
            avro_message = avro_encode(
                {
                    'data': message['data'],
                    'type': message['type']
                },
                self.avro_schema
            )
            self.producer.produce(Config.KAFKA_TOPIC, avro_message)
            ti.sleep(5)
            logger.info(f"Message sent to kafka: {message}")
        except Exception as e:
            logger.error(f"Failed to send message to kafka: {e}, message: {message}")

    def on_error(self, ws, error):
        max_retry = 5
        retry = 0
        if retry < max_retry:
            retry += 1
            self.ws.close()
            logger.warning(
                f"Retrying to connect to websocket, retry: {retry} out of {max_retry}"
            )
            ti.sleep(15)
            self.ws.run_forever()
        else:
            logger.error(f"Exceeded max retry, exiting...")
            self.ws.close()


    def on_close(self, ws):
        logger.info("### websocket is closing... ###")
        self.producer.flush(timeout=5)
        logger.info("### closed ###")


    def on_open(self, ws):
        try:
            for ticker in self.tickers:
                self.ws.send(f'{{"type": "subscribe", "symbol":"{ticker}"}}')
                logger.info(f"Subscribed to {ticker} successfully!")
        except Exception as e:
            logger.error(f"Subscribing to {ticker} failed: {e}")


if __name__ == "__main__":
   FinnhubProducer()