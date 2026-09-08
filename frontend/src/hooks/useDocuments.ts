import { useState, useCallback } from "react";
import { documentService } from "@/services/api/documents";
import type { Document, DocumentUploadResult } from "@/types/document";

export function useDocuments() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchDocuments = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await documentService.getList();
      setDocuments(data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setIsLoading(false);
    }
  }, []);

  const uploadDocument = useCallback(async (file: File): Promise<DocumentUploadResult> => {
    setIsUploading(true);
    try {
      const result = await documentService.upload(file);
      await fetchDocuments();
      return result;
    } finally {
      setIsUploading(false);
    }
  }, []);

  const deleteDocument = useCallback(async (documentId: string) => {
    await documentService.delete(documentId);
    setDocuments((prev) => prev.filter((d) => d.document_id !== documentId));
  }, []);

  return {
    documents,
    isLoading,
    isUploading,
    error,
    fetchDocuments,
    uploadDocument,
    deleteDocument,
  };
}
