"""Document processing background worker."""
import asyncio
import structlog

from backend.workers.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="backend.workers.document_processor.process_document", bind=True, max_retries=3)
def process_document(self, document_id: str, tenant_id: str, storage_path: str):
    """
    1. Download document from storage
    2. Extract text
    3. Run RAG ingestion (chunk → embed → index)
    4. Update document status
    """
    try:
        asyncio.run(_async_process(document_id, tenant_id, storage_path))
    except Exception as exc:
        logger.error("document_processing_failed", document_id=document_id, error=str(exc))
        raise self.retry(exc=exc, countdown=60)


async def _async_process(document_id: str, tenant_id: str, storage_path: str):
    from backend.infrastructure.storage.factory import get_storage
    from backend.ai.rag.pipeline import RAGPipeline

    storage = get_storage()
    # download() accepts both bare keys and full s3:// / gs:// URIs
    content_bytes = await storage.download(storage_path)
    text = content_bytes.decode("utf-8", errors="ignore")

    pipeline = RAGPipeline(tenant_id=tenant_id)
    chunk_count = await pipeline.ingest(document_id=document_id, text=text)

    logger.info("document_processed", document_id=document_id, chunk_count=chunk_count)
