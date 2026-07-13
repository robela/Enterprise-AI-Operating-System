"""Storage backend factory.

Selects S3 or GCS at runtime based on the STORAGE_BACKEND environment variable.

  STORAGE_BACKEND=s3   → boto3 / AWS S3  (default)
  STORAGE_BACKEND=gcs  → google-cloud-storage / GCP Cloud Storage
"""
from __future__ import annotations

from typing import Union

from backend.core.config.settings import settings


def get_storage() -> Union["GCSStorage", "S3Storage"]:  # type: ignore[name-defined]
    """Return a fully-initialised storage backend instance."""
    if settings.storage_backend == "gcs":
        from backend.infrastructure.storage.gcs import GCSStorage
        return GCSStorage()
    from backend.infrastructure.storage.s3 import S3Storage
    return S3Storage()
