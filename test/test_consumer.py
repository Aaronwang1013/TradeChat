import sys
import os
import pytest
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.sql.types import StructType, StructField, StringType, ArrayType, LongType, DoubleType
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from stock_price.streamimg_data.FinnhubConsumer.FinnhubConsumer import avro_decode, parse_df

@pytest.fixture(scope="module")
def spark():
    spark = SparkSession.builder.master("local[*]").appName("pyspark_test").getOrCreate()
    yield spark
    spark.stop()


def test_avro_decode(spark):
    schema = StructType([
        StructField("data", StructType([
            StructField("c", ArrayType(StringType()), True),
            StructField("p", ArrayType(DoubleType()), True),
            StructField("s", ArrayType(StringType()), True),
            StructField("t", ArrayType(LongType()), True),
            StructField("v", ArrayType(LongType()), True)
        ]), True)
    ])

    test_data = [
        ({"c": ["condition1"], "p": [100.0], "s": ["AAPL"], "t": [1622505600000], "v": [10]},)
    ]

    df = spark.createDataFrame(test_data, schema)
    decoded_df = avro_decode(df, schema)

    expected_schema = StructType([
        StructField("c", ArrayType(StringType()), True),
        StructField("p", ArrayType(DoubleType()), True),
        StructField("s", ArrayType(StringType()), True),
        StructField("t", ArrayType(LongType()), True),
        StructField("v", ArrayType(LongType()), True)
    ])

    assert decoded_df.schema == expected_schema
    assert decoded_df.count() == 1


def test_parse_df(spark):
    schema = StructType([
        StructField("c", ArrayType(StringType()), True),
        StructField("p", ArrayType(DoubleType()), True),
        StructField("s", ArrayType(StringType()), True),
        StructField("t", ArrayType(LongType()), True),
        StructField("v", ArrayType(LongType()), True)
    ])

    test_data = [
        (["condition1"], [100.0], ["AAPL"], [1622505600000], [10])
    ]

    df = spark.createDataFrame(test_data, schema)
    parsed_df = parse_df(df)

    expected_columns = {"trade_condition", "price", "symbol", "timestamp", "volume", "created_at"}
    assert expected_columns.issubset(set(parsed_df.columns))
    assert parsed_df.count() == 1

    row = parsed_df.collect()[0]
    assert row["trade_condition"] == "condition1"
    assert row["price"] == 100.0
    assert row["symbol"] == "AAPL"
    assert row["volume"] == 10
    assert "created_at" in row.asDict()
