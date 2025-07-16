import requests
from bs4 import BeautifulSoup
import yaml
from minio import Minio
from dotenv import load_dotenv
import os
import io
import time

load_dotenv()

def scrape_gutenberg():
    with open('sample_config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    client = Minio(
        os.getenv('MINIO_ENDPOINT'),
        access_key=os.getenv('MINIO_ACCESS_KEY'),
        secret_key=os.getenv('MINIO_SECRET_KEY'),
        secure=False
    )
    
    if not client.bucket_exists(config['minio']['bucket_raw']):
        client.make_bucket(config['minio']['bucket_raw'])
    
    base_url = config['scraper']['base_url']
    start_path = config['scraper']['start_path']
    max_pages = config['scraper']['max_pages']
    
    response = requests.get(base_url + start_path)
    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.select('a[href*="/ebooks/"]')[:max_pages]
    
    for link in links:
        time.sleep(1)  # Rate limiting
        href = link['href']
        if not href.startswith('http'):
            href = base_url + href
        book_response = requests.get(href)
        book_soup = BeautifulSoup(book_response.text, 'html.parser')
        text_link = book_soup.select_one('a[href*=".txt"]')
        if text_link:
            text_url = base_url + text_link['href']
            text_response = requests.get(text_url)
            client.put_object(
                config['minio']['bucket_raw'],
                f"books/{href.split('/')[-1]}.txt",
                data=io.BytesIO(text_response.content),
                length=len(text_response.content)
            )