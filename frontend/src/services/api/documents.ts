import { apiClient } from "./client";
import {
  documentSchema,
  documentUploadSchema,
  type Document,
  type DocumentUploadResult,
} from "@/types/document";

export const documentService = {
  async getList(): Promise<Document[]> {
    const { data } = await apiClient.get("/api/v1/documents");
    const items = Array.isArray((data as { items?: unknown[] })?.items)
      ? (data as { items: unknown[] }).items
      : [];
    return items.map((d) => documentSchema.parse(d));
  },

  async upload(file: File): Promise<DocumentUploadResult> {
    const form = new FormData();
    form.append("file", file);
    const { data } = await apiClient.post("/api/v1/documents", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return documentUploadSchema.parse(data);
  },

  async delete(documentId: string): Promise<void> {
    await apiClient.delete(`/api/v1/documents/${documentId}`);
  },
};
