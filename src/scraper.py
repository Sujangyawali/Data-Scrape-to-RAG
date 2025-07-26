import requests
from bs4 import BeautifulSoup
import yaml
from minio import Minio
from dotenv import load_dotenv
import os
import io
import time
import json

load_dotenv()

def scrape_gutenberg():
    with open('sample_config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    print("Loaded configuration.")

    client = Minio(
        os.getenv('MINIO_ENDPOINT'),
        access_key=os.getenv('MINIO_ACCESS_KEY'),
        secret_key=os.getenv('MINIO_SECRET_KEY'),
        secure=False
    )
    print("Initialized Minio client.")

    if not client.bucket_exists(config['minio']['bucket_raw']):
        client.make_bucket(config['minio']['bucket_raw'])
        print(f"Created bucket: {config['minio']['bucket_raw']}")
    else:
        print(f"Bucket already exists: {config['minio']['bucket_raw']}")

    base_url = config['scraper']['base_url']
    start_path = config['scraper']['start_path']
    max_pages = config['scraper']['max_pages']

    response = requests.get(base_url + start_path)
    print(f"Fetched start page: {base_url + start_path}")
    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.select('a[href*="/ebooks/"]')[:max_pages]
    print(f"Found {len(links)} ebook links.")

    for link in links:
        time.sleep(1)  # Rate limiting
        href = link['href']
        if not href.startswith('http'):
            href = base_url + href
        book_response = requests.get(href)
        print(f"Fetched book page: {href}")
        book_soup = BeautifulSoup(book_response.text, 'html.parser')
        
        text_link = book_soup.select_one('a[href*=".txt"]')
        
        if text_link:
            text_url = base_url + text_link['href']
            text_response = requests.get(text_url, headers={'Accept-Encoding': 'identity'})
            print(f"Fetched text file: {text_url}")

            # Read the content as binary to preserve the exact bytes
            content_bytes = text_response.content

            # Convert to string using the correct encoding (e.g., UTF-8), avoiding normalization
            content = content_bytes.decode('utf-8', errors='replace')

            combined_title = book_soup.select_one('h1') or book_soup.select_one('title')
            combined_title = combined_title.get_text(strip=True) if combined_title else "Unknown Title"

            # Split combined title to separate title and author
            if " by " in combined_title:
                title, author = combined_title.rsplit(" by ", 1)
                author = author.strip()
                title = title.strip()
            else:
                title = combined_title
                author = "Unknown Author"

            book_data = {
                "text_url": text_url,
                "title": title,
                "author": author,
                "content": content,
            }

            json_data = json.dumps(book_data, ensure_ascii=False)
            json_bytes = io.BytesIO(json_data.encode('utf-8'))
            
            client.put_object(
                config['minio']['bucket_raw'],
                f"books/{href.split('/')[-1]}.json",
                data=json_bytes,
                length=len(json_data.encode('utf-8')),
                content_type='application/json'
            )
            print(f"Uploaded book: books/{href.split('/')[-1]}.json")