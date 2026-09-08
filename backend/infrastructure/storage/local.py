"""Local filesystem storage adapter for development/testing."""
from __future__ import annotations

from pathlib import Path
import structlog

from backend.core.config.settings import settings

logger = structlog.get_logger(__name__)


class LocalStorage:
    def __init__(self):
        self._root = Path(settings.local_storage_path).resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def _normalize_key(self, key: str) -> str:
        if key.startswith("local://"):
            key = key[len("local://") :]
        return key.replace("\\", "/").lstrip("/")

    def _resolve_key_path(self, key: str) -> tuple[str, Path]:
        normalized_key = self._normalize_key(key)
        path = (self._root / normalized_key).resolve()
        if not str(path).startswith(str(self._root)):
            raise ValueError("Invalid storage key path")
        return normalized_key, path

    async def upload(
        self, key: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> str:
        normalized_key, path = self._resolve_key_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        logger.info("local_upload", key=normalized_key, content_type=content_type)
        return f"local://{normalized_key}"

    async def download(self, key: str) -> bytes:
        _, path = self._resolve_key_path(key)
        return path.read_bytes()

    async def delete(self, key: str) -> None:
        _, path = self._resolve_key_path(key)
        if path.exists():
            path.unlink()

    async def get_presigned_url(self, key: str, expiry_seconds: int = 3600) -> str:
        normalized_key, _ = self._resolve_key_path(key)
        return f"local://{normalized_key}"
