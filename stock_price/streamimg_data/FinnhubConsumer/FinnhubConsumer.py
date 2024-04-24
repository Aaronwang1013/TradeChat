from pyspark.sql import SparkSession
from pyspark.sql.functions import explode
from pyspark.sql.avro.functions import from_avro
from pyspark.sql.functions import col, current_timestamp, concat_ws, expr
from config import Config



import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

trades_schema = open("trades.avsc", "r").read()



def avro_decode(raw_df, schema):
    """
    decode avro data from kafka
    """
    try:
        decoded_df = (
            raw_df.withColumn("value", from_avro("value", schema))
            .select("value.*")
            .select('data.c', 'data.p', 'data.s', 'data.t', 'data.v')
        )
        return decoded_df
    except Exception as e:
        logger.error(f"Error in avro_decode: {e}, raw_df: {raw_df}")


def parse_df(decoded_df):
    try:
        parsed_df = (
            decoded_df.withColumnRenamed("c", "trade_condition")
                      .withColumnRenamed("p", "price")
                      .withColumnRenamed("s", "symbol")
                      .withColumnRenamed("t", "timestamp")
                      .withColumnRenamed("v", "volume")
                      .withColumn("timestamp", explode(col("timestamp")))
                      .withColumn(
                "timestamp", (col("timestamp") / 1000).cast("timestamp")
            )
            .withColumn("created_at", current_timestamp())
            .withColumn(
                "trade_condition",
                expr("transform(trade_condition, x -> cast(x as string))"),
            )
            .withColumn("trade_condition", concat_ws(",", col("trade_condition")))
            .withColumn("price", col("price")[0])
            .withColumn("volume", col("volume")[0])
            .withColumn("symbol", col("symbol")[0])
        )
        return parsed_df
    except Exception as e:
        logger.error(f"Error in parse_df: {e}, decoded_df: {decoded_df}")


if __name__ == "__main__":
    spark = (
        SparkSession.\
        builder.appName("finnhub_consumer").\
        master("local[*]").getOrCreate()
    )
    raw_df = spark \
        .readStream \
        .format("kafka") \
        .option("startingOffsets", "latest") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("subscribe", "TSLA,NVDA,AMZN,GOOG,AAPL,BTC,MSFT,META") \
        .load()
    
    decoded_df = avro_decode(raw_df, trades_schema)
    final_df = parse_df(decoded_df)

    
    dsw = (
        final_df.writeStream
            .format("mongodb")\
            .option("checkpointLocation", "/tmp/pyspark7/")\
            .option('spark.mongodb.connection.uri', f"mongodb+srv://{Config.MONGODB_USER}:{Config.MONGODB_PASSWORD}@cluster0.ibhiiti.mongodb.net/?retryWrites=true&w=secure&appName=Cluster0")\
            .option('spark.mongodb.database', 'TradeChat')\
            .option('spark.mongodb.collection', 'stock_realtime_price')\
            .start()
    )

    dsw.awaitTermination()  