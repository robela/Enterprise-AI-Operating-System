"""Storage backend factory.

Selects S3 or GCS at runtime based on the STORAGE_BACKEND environment variable.

  STORAGE_BACKEND=s3   → boto3 / AWS S3  (default)
  STORAGE_BACKEND=gcs  → google-cloud-storage / GCP Cloud Storage
"""
from __future__ import annotations

from typing import Union
import structlog

from backend.core.config.settings import settings


logger = structlog.get_logger(__name__)


def get_storage() -> Union["GCSStorage", "S3Storage", "LocalStorage"]:  # type: ignore[name-defined]
    """Return a fully-initialised storage backend instance."""
    if settings.storage_backend == "local":
        from backend.infrastructure.storage.local import LocalStorage

        return LocalStorage()

    if settings.storage_backend == "gcs":
        from backend.infrastructure.storage.gcs import GCSStorage

        return GCSStorage()

    if settings.storage_backend == "s3":
        # Local SQLite development commonly runs without cloud object-storage credentials.
        if settings.database_url.startswith("sqlite") and (
            not settings.aws_access_key_id or not settings.aws_secret_access_key
        ):
            from backend.infrastructure.storage.local import LocalStorage

            logger.warning(
                "storage_backend_fallback",
                requested_backend="s3",
                fallback_backend="local",
                reason="sqlite_local_dev_missing_aws_credentials",
            )
            return LocalStorage()

        from backend.infrastructure.storage.s3 import S3Storage

        return S3Storage()

    # Keep backward-compatible fallback behavior for unexpected values.
    from backend.infrastructure.storage.s3 import S3Storage

    return S3Storage()
