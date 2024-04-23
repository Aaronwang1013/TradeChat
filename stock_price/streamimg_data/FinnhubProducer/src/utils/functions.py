import json
import finnhub
import io
import avro.schema
import avro.io
from confluent_kafka import Producer



def load_client(token):
    return finnhub.Client(api_key=token)

def lookup_ticker(finnhub_client, ticker):
    return finnhub_client.symbol_lookup(ticker)

def ticker_validator(finnhub_client, ticker):
    for stock in lookup_ticker(finnhub_client, ticker)['result']:
        if stock['symbol'] == ticker:
            return True
    return False

def load_producer(kafka_server):
    # return Producer(bootstrap_servers=kafka_server)
    return Producer({'bootstrap.servers': kafka_server})

def load_avro_schema(schema_path):
    return avro.schema.parse(open(schema_path).read())



#encode message into avro format
def avro_encode(data, schema):
    writer = avro.io.DatumWriter(schema)
    bytes_writer = io.BytesIO()
    encoder = avro.io.BinaryEncoder(bytes_writer)
    writer.write(data, encoder)
    return bytes_writer.getvalue()