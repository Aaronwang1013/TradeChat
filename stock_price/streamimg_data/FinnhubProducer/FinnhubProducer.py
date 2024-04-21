import json
import websocket
from src.utils.functions import *
from src.utils.functions import avro_encode
from config import Config
import time as ti





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
            print("avro:" , avro_message)
            self.producer.produce(Config.KAFKA_TOPIC, avro_message)
            ti.sleep(5)
        except Exception as e:
            print(e)

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws):
        print("### closed ###")

    def on_open(self, ws):
        try:
            for ticker in self.tickers:
                self.ws.send(f'{{"type": "subscribe", "symbol":"{ticker}"}}')
        except Exception as e:
            print(e)


if __name__ == "__main__":
   FinnhubProducer()