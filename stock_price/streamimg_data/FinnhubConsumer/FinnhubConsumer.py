from pyspark.sql import SparkSession
from pyspark.sql.avro.functions import from_avro





# def avro_decode(data, schema):
#     try:
#         avro_decoded = (
#             data.withColumn("value", from_avro("value", schema))
#         )