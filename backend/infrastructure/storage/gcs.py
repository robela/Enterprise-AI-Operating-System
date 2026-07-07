"""Google Cloud Storage adapter."""
from __future__ import annotations

import datetime
import json

from google.cloud import storage
from google.oauth2 import service_account
import structlog

from backend.core.config.settings import settings

logger = structlog.get_logger(__name__)


class GCSStorage:
    def __init__(self):
        self._bucket_name = settings.gcs_bucket
        if settings.gcs_credentials_json:
            credentials = service_account.Credentials.from_service_account_info(
                json.loads(settings.gcs_credentials_json)
            )
            self._client = storage.Client(
                credentials=credentials, project=settings.gcs_project_id
            )
        else:
            # On Cloud Run, Application Default Credentials are injected automatically.
            self._client = storage.Client(project=settings.gcs_project_id or None)
        self._bucket = self._client.bucket(self._bucket_name)

    async def upload(
        self, key: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> str:
        blob = self._bucket.blob(key)
        blob.upload_from_string(data, content_type=content_type)
        logger.info("gcs_upload", bucket=self._bucket_name, key=key)
        return f"gs://{self._bucket_name}/{key}"

    async def download(self, key: str) -> bytes:
        """Accept either a bare key or a full gs:// URI."""
        prefix = f"gs://{self._bucket_name}/"
        if key.startswith(prefix):
            key = key[len(prefix):]
        blob = self._bucket.blob(key)
        return blob.download_as_bytes()

    async def delete(self, key: str) -> None:
        prefix = f"gs://{self._bucket_name}/"
        if key.startswith(prefix):
            key = key[len(prefix):]
        blob = self._bucket.blob(key)
        blob.delete()

    async def get_presigned_url(self, key: str, expiry_seconds: int = 3600) -> str:
        """Generate a V4 signed URL (requires a service-account credential)."""
        prefix = f"gs://{self._bucket_name}/"
        if key.startswith(prefix):
            key = key[len(prefix):]
        blob = self._bucket.blob(key)
        return blob.generate_signed_url(
            expiration=datetime.timedelta(seconds=expiry_seconds),
            method="GET",
            version="v4",
        )
