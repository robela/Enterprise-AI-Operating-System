import { apiClient } from "./client";
import {
  documentSchema,
  documentUploadSchema,
  type Document,
  type LifecycleStatus,
  type DocumentUploadOptions,
  type DocumentUploadResult,
} from "@/types/document";

const DOCUMENT_TRANSFER_TIMEOUT_MS = 120000;

export type DocumentChunkPreview = {
  index: number;
  text: string;
};

export type ExtractedWorkflow = {
  workflow_id: string;
  document_id: string;
  name: string;
  workflow_type: string;
  steps: string[];
  required_fields: string[];
  source_pages: number[];
  source_excerpt: string;
  confidence: string;
  status: "draft" | "approved" | "rejected";
};

export const documentService = {
  async getList(): Promise<Document[]> {
    const { data } = await apiClient.get("/api/v1/documents");
    const items = Array.isArray((data as { items?: unknown[] })?.items)
      ? (data as { items: unknown[] }).items
      : [];
    return items.map((d) => documentSchema.parse(d));
  },

  async upload(file: File, options?: DocumentUploadOptions): Promise<DocumentUploadResult> {
    const form = new FormData();
    form.append("file", file);
    if (options?.document_type) {
      form.append("document_type", options.document_type);
    }
    if (options?.lifecycle_status) {
      form.append("lifecycle_status", options.lifecycle_status);
    }
    const { data } = await apiClient.post("/api/v1/documents", form, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: DOCUMENT_TRANSFER_TIMEOUT_MS,
    });
    return documentUploadSchema.parse(data);
  },

  async update(
    documentId: string,
    file: File,
    options?: DocumentUploadOptions,
  ): Promise<DocumentUploadResult> {
    const form = new FormData();
    form.append("file", file);
    if (options?.document_type) {
      form.append("document_type", options.document_type);
    }
    if (options?.lifecycle_status) {
      form.append("lifecycle_status", options.lifecycle_status);
    }
    const { data } = await apiClient.put(`/api/v1/documents/${documentId}`, form, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: DOCUMENT_TRANSFER_TIMEOUT_MS,
    });
    return documentUploadSchema.parse(data);
  },

  async reingest(documentId: string): Promise<DocumentUploadResult> {
    const { data } = await apiClient.post(`/api/v1/documents/${documentId}/reingest`, undefined, {
      timeout: DOCUMENT_TRANSFER_TIMEOUT_MS,
    });
    return documentUploadSchema.parse(data);
  },

  async getContent(documentId: string): Promise<Blob> {
    const { data } = await apiClient.get(`/api/v1/documents/${documentId}/content`, {
      responseType: "blob",
    });
    return data as Blob;
  },

  async getPageCount(documentId: string): Promise<number | null> {
    const { data } = await apiClient.get<{ page_count?: number | null }>(`/api/v1/documents/${documentId}/page-count`);
    return typeof data.page_count === "number" ? data.page_count : null;
  },

  async getChunks(documentId: string): Promise<DocumentChunkPreview[]> {
    const { data } = await apiClient.get<{ items?: DocumentChunkPreview[] }>(`/api/v1/documents/${documentId}/chunks`, {
      params: { limit: 25 },
    });
    return Array.isArray(data.items) ? data.items : [];
  },

  async getExtractedWorkflows(documentId: string): Promise<ExtractedWorkflow[]> {
    const { data } = await apiClient.get<{ items?: ExtractedWorkflow[] }>(
      `/api/v1/documents/${documentId}/extracted-workflows`,
    );
    return Array.isArray(data.items) ? data.items : [];
  },

  async extractWorkflows(documentId: string): Promise<ExtractedWorkflow[]> {
    const { data } = await apiClient.post<{ items?: ExtractedWorkflow[] }>(
      `/api/v1/documents/${documentId}/extract-workflows`,
    );
    return Array.isArray(data.items) ? data.items : [];
  },

  async updateExtractedWorkflow(
    workflowId: string,
    update: Pick<ExtractedWorkflow, "name" | "steps" | "required_fields">,
  ): Promise<ExtractedWorkflow> {
    const { data } = await apiClient.patch<ExtractedWorkflow>(
      `/api/v1/documents/extracted-workflows/${workflowId}`,
      update,
    );
    return data;
  },

  async reviewExtractedWorkflow(
    workflowId: string,
    action: "approve" | "reject",
  ): Promise<ExtractedWorkflow> {
    const { data } = await apiClient.post<ExtractedWorkflow>(
      `/api/v1/documents/extracted-workflows/${workflowId}/${action}`,
    );
    return data;
  },

  async delete(documentId: string): Promise<void> {
    await apiClient.delete(`/api/v1/documents/${documentId}`);
  },

  async setLifecycleStatus(documentId: string, lifecycleStatus: LifecycleStatus): Promise<DocumentUploadResult> {
    const form = new FormData();
    form.append("lifecycle_status", lifecycleStatus);
    const { data } = await apiClient.patch(`/api/v1/documents/${documentId}/lifecycle`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return documentUploadSchema.parse(data);
  },
};
