"""AWS S3 object storage adapter."""
from __future__ import annotations

import boto3
from botocore.exceptions import ClientError
import structlog

from backend.core.config.settings import settings

logger = structlog.get_logger(__name__)


class S3Storage:
    def __init__(self):
        self._client = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )
        self._bucket = settings.aws_s3_bucket

    async def upload(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        logger.info("s3_upload", bucket=self._bucket, key=key)
        return f"s3://{self._bucket}/{key}"

    async def download(self, key: str) -> bytes:
        """Accept either a bare key or a full s3:// URI."""
        prefix = f"s3://{self._bucket}/"
        if key.startswith(prefix):
            key = key[len(prefix):]
        response = self._client.get_object(Bucket=self._bucket, Key=key)
        return response["Body"].read()

    async def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)

    async def get_presigned_url(self, key: str, expiry_seconds: int = 3600) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expiry_seconds,
        )
