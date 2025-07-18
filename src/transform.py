import sys
import os
from minio import Minio
import yaml

def bronze_to_silver():
    # Initialize MinIO client
    client = Minio(
        os.getenv('MINIO_ENDPOINT'),
        access_key=os.getenv('MINIO_ACCESS_KEY'),
        secret_key=os.getenv('MINIO_SECRET_KEY'),
        secure=False
    )
    
    # Load config
    with open('/opt/spark/sample_config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Define local data directory (mounted volume)
    data_dir = "/opt/spark/data"
    os.makedirs(data_dir, exist_ok=True)
    silver_dir = os.path.join(data_dir, "silver")
    os.makedirs(silver_dir, exist_ok=True)
    
    # List and download objects from bronze bucket to silver directory
    objects = client.list_objects(config['minio']['bucket_raw'], prefix="books/", recursive=True)
    for obj in objects:
        local_path = os.path.join(silver_dir, obj.object_name)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        client.fget_object(config['minio']['bucket_raw'], obj.object_name, local_path)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "bronze_to_silver":
        bronze_to_silver()