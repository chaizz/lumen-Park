from minio import Minio
from src.core.config import settings
import json

class MinioClient:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET
        self._ensure_bucket_exists()
        self._set_bucket_policy()

    def _ensure_bucket_exists(self):
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)

    def _set_bucket_policy(self):
        # Set public read policy
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{self.bucket_name}/*"]
                }
            ]
        }
        self.client.set_bucket_policy(self.bucket_name, json.dumps(policy))

    def upload_file(self, file_data, file_name, content_type):
        self.client.put_object(
            self.bucket_name,
            file_name,
            file_data,
            length=-1,
            part_size=10*1024*1024,
            content_type=content_type
        )
        # Return the URL
        protocol = "https" if settings.MINIO_SECURE else "http"
        return f"{protocol}://{settings.MINIO_ENDPOINT}/{self.bucket_name}/{file_name}"

minio_client = MinioClient()
