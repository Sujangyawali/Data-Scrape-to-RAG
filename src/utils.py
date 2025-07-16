from minio import Minio
import os
from dotenv import load_dotenv

load_dotenv()

def get_minio_client():
    return Minio(
        os.getenv('MINIO_ENDPOINT'),
        access_key=os.getenv('MINIO_ACCESS_KEY'),
        secret_key=os.getenv('MINIO_SECRET_KEY'),
        secure=False
    )

# </xaiArtifact»

#### 13. tests/test_scraper.py
# <xaiArtifact artifact_id="3973a2b8-a136-4b53-96ff-7197842142e5" artifact_version_id="3e9aa6c8-2675-4250-82b1-bb8a824c73c8" title="test_scraper.py" contentType="text/python">

import pytest
from src.scraper import scrape_gutenberg
from minio import Minio
import os

def test_scraper():
    scrape_gutenberg()
    client = Minio(
        os.getenv('MINIO_ENDPOINT'),
        access_key=os.getenv('MINIO_ACCESS_KEY'),
        secret_key=os.getenv('MINIO_SECRET_KEY'),
        secure=False
    )
    objects = list(client.list_objects("raw", prefix="books/", recursive=True))
    assert len(objects) > 0