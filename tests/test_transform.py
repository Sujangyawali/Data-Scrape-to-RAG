import pytest
from src.transform import bronze_to_silver, silver_to_gold
from pyspark.sql import SparkSession

def test_transform():
    spark = SparkSession.builder.appName("TestTransform").getOrCreate()
    bronze_to_silver()
    df_silver = spark.read.format("delta").load("s3a://gold/silver")
    assert df_silver.count() > 0
    silver_to_gold()
    df_gold = spark.read.format("delta").load("s3a://gold/gold")
    assert df_gold.count() > 0
    spark.stop()