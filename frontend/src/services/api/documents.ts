import { apiClient } from "./client";
import { documentSchema, type Document } from "@/types/document";

export const documentService = {
  async getList(): Promise<Document[]> {
    const { data } = await apiClient.get("/api/v1/documents");
    return (data as unknown[]).map((d) => documentSchema.parse(d));
  },

  async delete(id: number): Promise<void> {
    await apiClient.delete(`/api/v1/documents/${id}`);
  },
};
