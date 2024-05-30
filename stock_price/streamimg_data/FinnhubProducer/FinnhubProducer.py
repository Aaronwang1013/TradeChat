import json
import websocket
import threading
from src.utils.functions import load_client, load_producer, avro_encode, load_avro_schema
import time
from config import Config
import pytz
from datetime import datetime, time as dt_time
import time as ti

def is_market_open():
    ny_time = datetime.now(pytz.timezone('America/New_York'))
    start_time = dt_time(9, 0, 0)
    end_time = dt_time(16, 0, 0)
    return ny_time.weekday() < 5 and start_time <= ny_time.time() <= end_time

class FinnhubProducer:

    def __init__(self) -> None:
        self.finnhub_client = load_client(Config.FINN_API_KEY)
        self.producer = load_producer(f"{Config.KAFKA_SERVER}:{Config.KAFKA_PORT}")
        self.avro_schema = load_avro_schema('src/schema/trades.avsc')
        self.all_tickers = ["BINANCE:BTCUSDT", "TSLA", "NVDA", "AMZN", "AAPL", "GOOGL", "MSFT", "META"]
        self.btc_ticker = ["BINANCE:BTCUSDT"]
        self.ws = None
        self.ws_thread = None

    def start(self):
        while True:
            if is_market_open():
                print("market is open")
                self.tickers = self.all_tickers
            else:
                print("market is closed")
                self.tickers = self.btc_ticker

            self.run_websocket()
            ti.sleep(60*30)  

    def run_websocket(self):
        if self.ws:
            self.ws.close()

        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(f"wss://ws.finnhub.io?token={Config.FINN_API_KEY}",
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close)
        self.ws.on_open = self.on_open
        self.ws_thread = threading.Thread(target=self.ws.run_forever)
        self.ws_thread.start()

    def on_message(self, ws, message):
        message = json.loads(message)
        for i in message['data']:
            ticker = i['s']
            if ticker == 'BINANCE:BTCUSDT':
                topic = 'BTC'
            elif ticker == 'TSLA':
                topic = 'TSLA'
            elif ticker == 'NVDA':
                topic = 'NVDA'
            elif ticker == 'AMZN':
                topic = 'AMZN'
            elif ticker == 'GOOGL':
                topic = 'GOOG'
            elif ticker == 'MSFT':
                topic = 'MSFT'
            elif ticker == 'AAPL':
                topic = 'AAPL'
            elif ticker == 'META':
                topic = 'META'
            else:
                continue 
            try:
                avro_message = avro_encode({'data': [i]}, self.avro_schema)
                self.producer.produce(topic, avro_message)
                self.producer.flush() 
            except Exception as e:
                print(e)

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws, close_status_code, close_msg):
        print("### closed ###")

    def on_open(self, ws):
        for ticker in self.tickers:
            self.ws.send(json.dumps({"type": "subscribe", "symbol": ticker}))

if __name__ == "__main__":
    producer = FinnhubProducer()
    producer.start()
