from pyspark.sql import SparkSession
from pyspark.sql.avro.functions import from_avro
from confluent_kafka.serialization import StringDeserializer, MessageField
from confluent_kafka.avro import AvroConsumer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer



spark = (
        SparkSession.builder.appName("finnhub_consumer").master("local[*]").getOrCreate()
    )
raw_df = (spark.readStream.format("kafka")
          .option("kafka.bootstrap.servers", "kafka:9092")
          .option("subscribe", "market").load()
          .option("startingOffsets", "latest")
        )


print(raw_df)


def avro_decode(data, schema):
    try:
        avro_decoded = (
            data.withColumn("value", from_avro("value", schema))
        )
    except Exception as e:
        print(e)