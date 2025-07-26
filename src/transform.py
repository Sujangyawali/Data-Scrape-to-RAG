import sys
import os
from minio import Minio
import yaml
import json
import csv
import io

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
    
    # Check and create gold bucket if it doesn't exist
    gold_bucket = config['minio'].get('bucket_gold', 'gold')
    if not client.bucket_exists(gold_bucket):
        client.make_bucket(gold_bucket)
        print(f"Created bucket: {gold_bucket}")
    else:
        print(f"Bucket already exists: {gold_bucket}")

    # List and process JSON objects from bronze bucket
    objects = client.list_objects(config['minio']['bucket_raw'], prefix="books/", recursive=True)
    for obj in objects:
        if obj.object_name.endswith('.json'):
            # Download JSON file
            response = client.get_object(config['minio']['bucket_raw'], obj.object_name)
            json_data = json.loads(response.read().decode('utf-8'))
            response.close()
            response.release_conn()
            
            # Prepare CSV file path
            csv_filename = os.path.splitext(obj.object_name)[0] + '.csv'
            local_path = os.path.join(silver_dir, csv_filename)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Get JSON keys as CSV headers
            headers = list(json_data.keys())
            
            # Write to CSV
            with open(local_path, 'w', newline='', encoding='utf-8') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=headers)
                writer.writeheader()
                writer.writerow(json_data)
            
            print(f"Converted {obj.object_name} to CSV at {local_path}")
            
            # Upload CSV to gold bucket
            with open(local_path, 'rb') as file_data:
                file_stat = os.stat(local_path)
                client.put_object(
                    gold_bucket,
                    csv_filename,
                    data=io.BytesIO(file_data.read()),
                    length=file_stat.st_size,
                    content_type='text/csv'
                )
            print(f"Uploaded CSV to gold bucket: {csv_filename}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "bronze_to_silver":
        bronze_to_silver()