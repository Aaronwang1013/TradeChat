import json
import websocket
from src.utils.functions import *
from src.utils.functions import avro_encode
import time
from config import Config
import pytz
from datetime import datetime, time
import time as ti




def is_market_open():
    ny_time = datetime.now(pytz.timezone('America/New_York'))
    start_time = time(9, 30, 0)
    end_time = time(16, 0, 0)
    # if market is open
    return True
    # return ny_time.weekday() < 5 and start_time <= ny_time.time() <= end_time


class FinnhubProducer:

    def __init__(self) -> None:
        self.finnhub_client = load_client(Config.FINN_API_KEY)
        self.producer = load_producer(f"{Config.KAFKA_SERVER}:{Config.KAFKA_PORT}")
        self.avro_schema = load_avro_schema('src/schema/trades.avsc')
        self.tickers = ["BINANCE:BTCUSDT", "TSLA", "NVDA", "AMZN", "AAPL", "GOOGL", "MSFT", "META"]
        # self.tickers = ["BINANCE:BTCUSDT", "BINANCE:ETHUSDT"]
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
        for i in message['data']:
            if i['s'] == 'BINANCE:BTCUSDT':                
                try:
                    avro_message = avro_encode(
                        {
                            'data': [i]
                        },
                        self.avro_schema
                    )
                    self.producer.produce('BTC', avro_message)
                except Exception as e:
                    print(e)

            if i['s'] == 'TSLA':                
                try:
                    avro_message = avro_encode(
                        {
                            'data': [i]
                        },
                        self.avro_schema
                    )
                    self.producer.produce('TSLA', avro_message)
                except Exception as e:
                    print(e)
            elif i['s'] == 'NVDA':
                try:
                    avro_message = avro_encode(
                        {
                            'data': [i]
                        },
                        self.avro_schema
                    )
                    self.producer.produce('NVDA', avro_message)
                except Exception as e:
                    print(e)
            elif i['s'] == 'AMZN':
                try:
                    avro_message = avro_encode(
                        {
                            'data': [i]
                        },
                        self.avro_schema
                    )
                    self.producer.produce('AMZN', avro_message)
                except Exception as e:
                    print(e)

            elif i['s'] == 'GOOGL':
                try:
                    avro_message = avro_encode(
                        {
                            'data': [i]
                        },
                        self.avro_schema
                    )
                    self.producer.produce('GOOG', avro_message)
                except Exception as e:
                    print(e)
            elif i['s'] == 'MSFT':
                try:
                    avro_message = avro_encode(
                        {
                            'data': [i]
                        },
                        self.avro_schema
                    )
                    self.producer.produce('MSFT', avro_message)
                except Exception as e:
                    print(e)
                
            elif i['s'] == 'AAPL':
                try:
                    avro_message = avro_encode(
                        {
                            'data': [i]
                        },
                        self.avro_schema
                    )
                    self.producer.produce('AAPL', avro_message)
                except Exception as e:
                    print(e)
                
            elif i['s'] == 'META':
                try:
                    avro_message = avro_encode(
                        {
                            'data': [i]
                        },
                        self.avro_schema
                    )
                    self.producer.produce('META', avro_message)
                except Exception as e:
                    print(e)
        ti.sleep(5)
                

    def on_error(self, ws, error):
        print(error)

    def on_close(self, ws):
        print("### closed ###")

    def on_open(self, ws):
        if is_market_open():
            for ticker in self.tickers:
                # self.ws.send(f'{{"type": "subscribe", "symbol":"{ticker}"}}')
                self.ws.send(json.dumps({"type": "subscribe", "symbol": ticker}))
        else:
            print("Market is closed")
            self.ws.close()


if __name__ == "__main__":
    while True:
        if is_market_open():
            FinnhubProducer()
        else:
            ti.sleep(60*10)