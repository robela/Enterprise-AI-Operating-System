"use client";

import { useEffect } from "react";
import { useDocuments } from "@/hooks/useDocuments";
import { toast } from "sonner";

export function DocumentsClient() {
  const { documents, isLoading, error, fetchDocuments, deleteDocument } =
    useDocuments();

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleDelete = async (id: number) => {
    try {
      await deleteDocument(id);
      toast.success("Document deleted");
    } catch {
      toast.error("Failed to delete document");
    }
  };

  if (error) {
    return (
      <div className="text-destructive text-sm">
        Failed to load documents: {error.message}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Documents</h1>

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div
              key={i}
              className="h-12 bg-muted animate-pulse rounded-lg"
            />
          ))}
        </div>
      ) : documents.length === 0 ? (
        <div className="border rounded-lg p-12 text-center">
          <p className="text-muted-foreground">No documents uploaded yet.</p>
        </div>
      ) : (
        <div className="border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted">
              <tr>
                <th className="text-left px-4 py-3 font-medium">Name</th>
                <th className="text-left px-4 py-3 font-medium">Type</th>
                <th className="text-left px-4 py-3 font-medium">Size</th>
                <th className="text-left px-4 py-3 font-medium">Uploaded</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id} className="border-t hover:bg-muted/50">
                  <td className="px-4 py-3 font-medium">{doc.name}</td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {doc.content_type}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {(doc.size_bytes / 1024).toFixed(1)} KB
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {new Date(doc.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => handleDelete(doc.id)}
                      className="text-xs px-3 py-1 rounded border border-destructive text-destructive hover:bg-destructive hover:text-destructive-foreground transition-colors"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
