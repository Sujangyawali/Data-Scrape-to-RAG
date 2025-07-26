import duckdb
import yaml
import os
from dotenv import load_dotenv

def query_csv_data():
    # Load environment variables
    load_dotenv()
    MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT')
    MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY')
    MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY')
    print(f"Using MinIO endpoint: {MINIO_ENDPOINT}")



    # Load config
    with open('/app/sample_config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Initialize DuckDB connection
    con = duckdb.connect()

    # Install and load httpfs extension for S3 access
    con.execute("INSTALL httpfs")
    con.execute("LOAD httpfs")
    con.execute("SET s3_url_style = 'path';")

    # Configure S3 access for MinIO
    con.execute(f"""
        SET s3_endpoint = '{MINIO_ENDPOINT}';
        SET s3_access_key_id = '{MINIO_ACCESS_KEY}';
        SET s3_secret_access_key = '{MINIO_SECRET_KEY}';
        SET s3_use_ssl = false;
        SET s3_url_style = 'path';
    """)

    # Get gold bucket name
    gold_bucket = config['minio'].get('bucket_gold', 'gold')
    print(f"Using gold bucket: {gold_bucket}")

    # Query CSV files from gold bucket
    csv_query = f"""
        SELECT title as book
        FROM read_csv('s3://{gold_bucket}/books/*.csv', header=true)
        where author like '%William Shakespeare%'
        LIMIT 10
    """
    print("Executing CSV query...")
    result = con.execute(csv_query).fetchdf()
    print("CSV Query Result:")
    print(result)


    # Close connection
    con.close()

if __name__ == "__main__":
    query_csv_data()