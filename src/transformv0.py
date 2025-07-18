from pyspark.sql import SparkSession
from minio import Minio
from dotenv import load_dotenv
import os
import yaml

load_dotenv()

def bronze_to_silver():
    spark = SparkSession.builder.appName("BronzeToSilver").getOrCreate()
    client = Minio(
        os.getenv('MINIO_ENDPOINT'),
        access_key=os.getenv('MINIO_ACCESS_KEY'),
        secret_key=os.getenv('MINIO_SECRET_KEY'),
        secure=False
    )
    with open('sample_config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    objects = client.list_objects(config['minio']['bucket_raw'], prefix="books/", recursive=True)
    paths = [f"s3a://{config['minio']['bucket_raw']}/{obj.object_name}" for obj in objects]
    df = spark.read.text(paths)
    df_clean = df.filter(df.value.isNotNull()).selectExpr("value as text", "input_file_name() as source")
    df_clean.write.mode("overwrite").format("delta").save(f"s3a://{config['minio']['bucket_gold']}/silver")
    spark.stop()

def silver_to_gold():
    spark = SparkSession.builder.appName("SilverToGold").getOrCreate()
    with open('sample_config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    df = spark.read.format("delta").load(f"s3a://{config['minio']['bucket_gold']}/silver")
    df_gold = df.selectExpr(
        "text",
        "source",
        "current_timestamp() as timestamp",
        "length(text) as text_length"
    )
    df_gold.write.mode("overwrite").format("delta").save(f"s3a://{config['minio']['bucket_gold']}/gold")
    spark.stop()