"""Elasticsearch full-text search adapter."""
from __future__ import annotations

from elasticsearch import AsyncElasticsearch
import structlog

from backend.core.config.settings import settings

logger = structlog.get_logger(__name__)


class ElasticsearchAdapter:
    def __init__(self):
        self._client = AsyncElasticsearch(settings.elasticsearch_url)
        self._prefix = settings.elasticsearch_index_prefix

    def _index(self, tenant_id: str, resource: str) -> str:
        return f"{self._prefix}_{tenant_id}_{resource}"

    async def index_document(self, tenant_id: str, resource: str, doc_id: str, body: dict) -> None:
        idx = self._index(tenant_id, resource)
        await self._client.index(index=idx, id=doc_id, body=body)
        logger.debug("es_indexed", index=idx, doc_id=doc_id)

    async def search(
        self, tenant_id: str, resource: str, query: str, size: int = 10
    ) -> list[dict]:
        idx = self._index(tenant_id, resource)
        response = await self._client.search(
            index=idx,
            body={"query": {"multi_match": {"query": query, "fields": ["*"]}}},
            size=size,
        )
        return [hit["_source"] for hit in response["hits"]["hits"]]

    async def delete_document(self, tenant_id: str, resource: str, doc_id: str) -> None:
        idx = self._index(tenant_id, resource)
        await self._client.delete(index=idx, id=doc_id, ignore=[404])

    async def close(self) -> None:
        await self._client.close()
