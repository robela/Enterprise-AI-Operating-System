import pytest
from sqlalchemy import select

from backend.core.security.jwt import create_access_token
from backend.infrastructure.persistence.models import DocumentModel


class StubStorage:
    def __init__(self) -> None:
        self.upload_calls: list[dict] = []
        self.delete_calls: list[str] = []

    async def upload(self, key: str, content: bytes, content_type: str) -> str:
        self.upload_calls.append(
            {
                "key": key,
                "content": content,
                "content_type": content_type,
            }
        )
        return f"local://{key}"

    async def delete(self, storage_path: str) -> None:
        self.delete_calls.append(storage_path)

    async def download(self, storage_path: str) -> bytes:
        return b"placeholder PDF content"


@pytest.fixture
def document_dependency_stubs(monkeypatch):
    from backend.api.rest import documents_router

    storage = StubStorage()
    pipeline_instances: list["StubRAGPipeline"] = []

    class StubRAGPipeline:
        def __init__(self, tenant_id: str):
            self.tenant_id = tenant_id
            self.deleted_document_ids: list[str] = []
            self.ingest_calls: list[dict] = []
            pipeline_instances.append(self)

        async def ingest(self, document_id: str, text: str, metadata: dict | None = None) -> int:
            self.ingest_calls.append(
                {
                    "document_id": document_id,
                    "text": text,
                    "metadata": metadata or {},
                }
            )
            return 3

        async def delete_document(self, document_id: str) -> None:
            self.deleted_document_ids.append(document_id)

    monkeypatch.setattr(documents_router, "get_storage", lambda: storage)
    monkeypatch.setattr(documents_router, "RAGPipeline", StubRAGPipeline)

    return {
        "storage": storage,
        "pipelines": pipeline_instances,
    }


def _token(*, user_id: str, tenant_id: str) -> str:
    return create_access_token(
        user_id,
        extra_claims={
            "tenant_id": tenant_id,
            "roles": ["admin"],
            "scopes": ["admin"],
        },
    )


@pytest.mark.asyncio
async def test_upload_document_indexes_and_persists(client, db_session, document_dependency_stubs) -> None:
    token = _token(user_id="doc-user-1", tenant_id="tenant-doc-a")

    response = await client.post(
        "/api/v1/documents",
        headers={"Authorization": f"Bearer {token}"},
        data={"document_type": "primary", "lifecycle_status": "inactive"},
        files={"file": ("notes.txt", b"hello from upload", "text/plain")},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "indexed"
    assert payload["chunk_count"] == 3
    assert payload["doc_type"] == "primary"
    assert payload["lifecycle_status"] == "inactive"

    storage = document_dependency_stubs["storage"]
    assert len(storage.upload_calls) == 1
    assert storage.upload_calls[0]["key"] == "tenant-doc-a/documents/notes.txt"

    pipelines = document_dependency_stubs["pipelines"]
    assert len(pipelines) == 1
    assert pipelines[0].tenant_id == "tenant-doc-a"
    assert len(pipelines[0].ingest_calls) == 1
    assert pipelines[0].ingest_calls[0]["document_id"] == payload["document_id"]

    persisted = await db_session.scalar(
        select(DocumentModel).where(DocumentModel.document_id == payload["document_id"])
    )
    assert persisted is not None
    assert persisted.tenant_id == "tenant-doc-a"
    assert persisted.filename == "notes.txt"
    assert persisted.doc_type == "primary"
    assert persisted.status == "indexed"
    assert persisted.chunk_count == 3
    assert (persisted.metadata_ or {}).get("lifecycle_status") == "inactive"


@pytest.mark.asyncio
async def test_upload_document_returns_service_unavailable_when_storage_fails(
    client, document_dependency_stubs, monkeypatch
) -> None:
    from backend.api.rest import documents_router

    async def fail_upload(*_args, **_kwargs) -> str:
        raise RuntimeError("GCS bucket access denied")

    monkeypatch.setattr(document_dependency_stubs["storage"], "upload", fail_upload)
    token = _token(user_id="doc-user-storage-failure", tenant_id="tenant-doc-storage-failure")

    response = await client.post(
        "/api/v1/documents",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("notes.txt", b"hello from upload", "text/plain")},
    )

    assert response.status_code == 503
    assert response.json() == {
        "error": "SERVICE_UNAVAILABLE",
        "message": "Document storage is temporarily unavailable. Please try again later.",
    }


@pytest.mark.asyncio
async def test_reingest_document_retries_failed_document(client, db_session, document_dependency_stubs) -> None:
    token = _token(user_id="doc-user-retry", tenant_id="tenant-doc-retry")
    create_response = await client.post(
        "/api/v1/documents",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("retry.txt", b"retry document", "text/plain")},
    )
    assert create_response.status_code == 201
    document_id = create_response.json()["document_id"]

    document = await db_session.scalar(
        select(DocumentModel).where(DocumentModel.document_id == document_id)
    )
    assert document is not None
    document.status = "failed"
    await db_session.commit()

    response = await client.post(
        f"/api/v1/documents/{document_id}/reingest",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "indexed"
    assert response.json()["chunk_count"] == 3
    assert len(document_dependency_stubs["pipelines"]) == 2


@pytest.mark.asyncio
async def test_replace_document_reindexes_and_cleans_old_storage(client, db_session, document_dependency_stubs) -> None:
    token = _token(user_id="doc-user-2", tenant_id="tenant-doc-b")

    create_response = await client.post(
        "/api/v1/documents",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("policy-v1.txt", b"version one", "text/plain")},
    )
    assert create_response.status_code == 201
    document_id = create_response.json()["document_id"]

    replace_response = await client.put(
        f"/api/v1/documents/{document_id}",
        headers={"Authorization": f"Bearer {token}"},
        data={"document_type": "secondary", "lifecycle_status": "active"},
        files={"file": ("policy-v2.txt", b"version two", "text/plain")},
    )

    assert replace_response.status_code == 200
    payload = replace_response.json()
    assert payload["document_id"] == document_id
    assert payload["status"] == "indexed"
    assert payload["chunk_count"] == 3
    assert payload["doc_type"] == "secondary"
    assert payload["lifecycle_status"] == "active"

    storage = document_dependency_stubs["storage"]
    assert len(storage.upload_calls) == 2
    assert storage.upload_calls[0]["key"] == "tenant-doc-b/documents/policy-v1.txt"
    assert storage.upload_calls[1]["key"] == f"tenant-doc-b/documents/{document_id}/policy-v2.txt"
    assert storage.delete_calls == ["local://tenant-doc-b/documents/policy-v1.txt"]

    pipelines = document_dependency_stubs["pipelines"]
    assert len(pipelines) == 2
    assert pipelines[1].deleted_document_ids == [document_id]
    assert len(pipelines[1].ingest_calls) == 1
    assert pipelines[1].ingest_calls[0]["document_id"] == document_id

    persisted = await db_session.scalar(
        select(DocumentModel).where(DocumentModel.document_id == document_id)
    )
    assert persisted is not None
    assert persisted.filename == "policy-v2.txt"
    assert persisted.storage_path == f"local://tenant-doc-b/documents/{document_id}/policy-v2.txt"
    assert persisted.doc_type == "secondary"
    assert persisted.status == "indexed"
    assert (persisted.metadata_ or {}).get("lifecycle_status") == "active"


@pytest.mark.asyncio
async def test_delete_document_removes_record_and_vector_chunks(client, db_session, document_dependency_stubs) -> None:
    token = _token(user_id="doc-user-3", tenant_id="tenant-doc-c")

    create_response = await client.post(
        "/api/v1/documents",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("cleanup.txt", b"cleanup me", "text/plain")},
    )
    assert create_response.status_code == 201
    document_id = create_response.json()["document_id"]

    delete_response = await client.delete(
        f"/api/v1/documents/{document_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert delete_response.status_code == 204

    persisted = await db_session.scalar(
        select(DocumentModel).where(DocumentModel.document_id == document_id)
    )
    assert persisted is None

    storage = document_dependency_stubs["storage"]
    assert storage.delete_calls == ["local://tenant-doc-c/documents/cleanup.txt"]

    pipelines = document_dependency_stubs["pipelines"]
    assert len(pipelines) == 2
    assert pipelines[1].deleted_document_ids == [document_id]


@pytest.mark.asyncio
async def test_replace_document_rejects_cross_tenant_access(client, document_dependency_stubs) -> None:
    owner_token = _token(user_id="doc-owner", tenant_id="tenant-doc-owner")
    other_token = _token(user_id="doc-other", tenant_id="tenant-doc-other")

    create_response = await client.post(
        "/api/v1/documents",
        headers={"Authorization": f"Bearer {owner_token}"},
        files={"file": ("owner.txt", b"owner text", "text/plain")},
    )
    assert create_response.status_code == 201
    document_id = create_response.json()["document_id"]

    replace_response = await client.put(
        f"/api/v1/documents/{document_id}",
        headers={"Authorization": f"Bearer {other_token}"},
        files={"file": ("hijack.txt", b"hijack", "text/plain")},
    )

    assert replace_response.status_code == 404
    assert "not found" in replace_response.json()["message"].lower()


@pytest.mark.asyncio
async def test_completeness_candidates_are_tenant_scoped_and_page_backed(
    client, document_dependency_stubs, monkeypatch
) -> None:
    from backend.api.rest import documents_router

    token = _token(user_id="imci-reviewer", tenant_id="tenant-imci")
    create_response = await client.post(
        "/api/v1/documents",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("IMCI-guidelines.pdf", b"placeholder", "application/pdf")},
    )
    document_id = create_response.json()["document_id"]
    monkeypatch.setattr(
        documents_router,
        "extract_pdf_pages",
        lambda content: ["Assess ability to drink.", "Measure the child's temperature."],
    )

    response = await client.get(
        f"/api/v1/documents/{document_id}/completeness-candidates",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "document_id": document_id,
        "items": [
            {"text": "Assess ability to drink.", "page_number": 1},
            {"text": "Measure the child's temperature.", "page_number": 2},
        ],
        "review_required": True,
    }


@pytest.mark.asyncio
async def test_approved_workflow_reports_only_missing_required_fields(
    client, document_dependency_stubs, monkeypatch
) -> None:
    from backend.api.rest import documents_router

    token = _token(user_id="workflow-reviewer", tenant_id="tenant-workflow")
    create_response = await client.post(
        "/api/v1/documents",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("IMCI-guidelines.pdf", b"placeholder", "application/pdf")},
    )
    document_id = create_response.json()["document_id"]
    monkeypatch.setattr(
        documents_router,
        "extract_pdf_pages",
        lambda content: [
            "Ask the child's age. Check for general danger signs. "
            "Ask about main symptoms. Check nutrition and immunization status."
        ],
    )

    extracted = await client.post(
        f"/api/v1/documents/{document_id}/extract-workflows",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert extracted.status_code == 200
    workflow = extracted.json()["items"][0]
    assert workflow["status"] == "draft"

    before_approval = await client.post(
        f"/api/v1/documents/extracted-workflows/{workflow['workflow_id']}/completeness-check",
        headers={"Authorization": f"Bearer {token}"},
        json={"facts": {"child_age": "3 years"}},
    )
    assert before_approval.status_code == 422

    approval = await client.post(
        f"/api/v1/documents/extracted-workflows/{workflow['workflow_id']}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert approval.status_code == 200
    assert approval.json()["status"] == "approved"

    checked = await client.post(
        f"/api/v1/documents/extracted-workflows/{workflow['workflow_id']}/completeness-check",
        headers={"Authorization": f"Bearer {token}"},
        json={"facts": {"child_age": "3 years", "main_symptoms": "fever"}},
    )
    assert checked.status_code == 200
    assert checked.json()["missing_fields"] == [
        "general_danger_signs",
        "nutrition_status",
        "immunization_status",
    ]
