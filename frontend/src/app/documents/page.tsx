"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AxiosError } from "axios";
import { toast } from "sonner";

import { apiClient } from "@/services/api/client";
import { useAuth } from "@/utils/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

type DocumentStatus = "pending" | "processing" | "indexed" | "failed";

interface TenantDocument {
  document_id: string;
  filename: string;
  status: DocumentStatus;
}

interface ListResponse {
  items: TenantDocument[];
}

interface UploadResponse {
  document_id: string;
  status: DocumentStatus;
  chunk_count: number;
}

interface TenantListItem {
  tenant_id: string;
  name: string;
  is_active: boolean;
}

function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof AxiosError) {
    const payload = error.response?.data as { message?: string; detail?: string } | undefined;
    return payload?.message || payload?.detail || error.message || fallback;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return fallback;
}

function statusClass(status: DocumentStatus): string {
  if (status === "indexed") return "bg-emerald-100 text-emerald-700";
  if (status === "processing") return "bg-amber-100 text-amber-700";
  if (status === "failed") return "bg-rose-100 text-rose-700";
  return "bg-slate-100 text-slate-700";
}

export default function DocumentsPage() {
  const { tenant_id } = useAuth();
  const [documents, setDocuments] = useState<TenantDocument[]>([]);
  const [tenantOptions, setTenantOptions] = useState<TenantListItem[]>([]);
  const [tenantOptionsLoading, setTenantOptionsLoading] = useState(false);
  const [selectedTenantViewId, setSelectedTenantViewId] = useState(tenant_id ?? "");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const tenantLabel = useMemo(() => tenant_id || "unknown", [tenant_id]);
  const activeTenantId = tenant_id ?? "";
  const isTenantMismatch = Boolean(selectedTenantViewId && activeTenantId && selectedTenantViewId !== activeTenantId);
  const selectedTenantLoginHref = useMemo(() => {
    if (!selectedTenantViewId) {
      return "/login";
    }
    return `/login?tenant=${encodeURIComponent(selectedTenantViewId)}`;
  }, [selectedTenantViewId]);

  const loadTenantOptions = useCallback(async () => {
    setTenantOptionsLoading(true);
    try {
      const { data } = await apiClient.get<TenantListItem[]>("/api/v1/tenants", {
        params: {
          include_inactive: false,
          skip: 0,
          limit: 200,
        },
      });

      const list = Array.isArray(data) ? data : [];
      const activeInList = activeTenantId ? list.some((tenant) => tenant.tenant_id === activeTenantId) : true;
      const withActiveTenant = !activeInList && activeTenantId
        ? [{ tenant_id: activeTenantId, name: activeTenantId, is_active: true }, ...list]
        : list;

      setTenantOptions(withActiveTenant);
      setSelectedTenantViewId((prev) => prev || activeTenantId);
    } catch {
      if (activeTenantId) {
        setTenantOptions([{ tenant_id: activeTenantId, name: activeTenantId, is_active: true }]);
        setSelectedTenantViewId((prev) => prev || activeTenantId);
      } else {
        setTenantOptions([]);
      }
    } finally {
      setTenantOptionsLoading(false);
    }
  }, [activeTenantId]);

  useEffect(() => {
    if (activeTenantId) {
      setSelectedTenantViewId((prev) => prev || activeTenantId);
    }
  }, [activeTenantId]);

  useEffect(() => {
    void loadTenantOptions();
  }, [loadTenantOptions]);

  const fetchDocuments = useCallback(async () => {
    setIsLoading(true);
    try {
      const { data } = await apiClient.get<ListResponse>("/api/v1/documents");
      setDocuments(Array.isArray(data?.items) ? data.items : []);
    } catch (error) {
      toast.error(getErrorMessage(error, "Failed to load tenant documents"));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchDocuments();
  }, [fetchDocuments]);

  const onUpload = async () => {
    if (!selectedFile) {
      toast.error("Choose a file to upload");
      return;
    }

    if (isTenantMismatch) {
      toast.error("Selected tenant does not match your signed-in tenant");
      return;
    }

    setIsUploading(true);
    try {
      const form = new FormData();
      form.append("file", selectedFile);
      const { data } = await apiClient.post<UploadResponse>("/api/v1/documents", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      toast.success(`Uploaded ${data.document_id} (${data.status})`);
      setSelectedFile(null);
      const input = document.getElementById("doc-upload-input") as HTMLInputElement | null;
      if (input) input.value = "";
      await fetchDocuments();
    } catch (error) {
      toast.error(getErrorMessage(error, "Upload failed"));
    } finally {
      setIsUploading(false);
    }
  };

  const onDelete = async (documentId: string) => {
    if (isTenantMismatch) {
      toast.error("Selected tenant does not match your signed-in tenant");
      return;
    }

    setDeletingId(documentId);
    try {
      await apiClient.delete(`/api/v1/documents/${documentId}`);
      toast.success("Document deleted");
      setDocuments((prev) => prev.filter((doc) => doc.document_id !== documentId));
    } catch (error) {
      toast.error(getErrorMessage(error, "Delete failed"));
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Document Management</h1>
          <p className="text-sm text-muted-foreground">
            Tenant-scoped document library. You only see documents for your active tenant.
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Active tenant: <span className="font-semibold text-foreground">{tenantLabel}</span>
          </p>
        </div>

        <Button
          type="button"
          variant="outline"
          onClick={() => void fetchDocuments()}
          disabled={isLoading || isTenantMismatch}
        >
          {isLoading ? "Refreshing..." : "Refresh"}
        </Button>
      </div>

      <section className="rounded-lg border bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold">Tenant Scope</h2>
        <p className="mt-1 text-xs text-muted-foreground">
          Documents are isolated by tenant. API calls use the signed-in tenant shown below.
        </p>

        <div className="mt-4 grid gap-3 md:grid-cols-[280px_1fr] md:items-center">
          <label htmlFor="tenant-view-select" className="text-sm font-medium">
            Select tenant to view context
          </label>
          <select
            id="tenant-view-select"
            value={selectedTenantViewId}
            onChange={(event) => setSelectedTenantViewId(event.target.value)}
            className="h-10 rounded-md border px-3 text-sm"
          >
            {!tenantOptions.length && <option value="">No tenant available</option>}
            {tenantOptions.map((tenant) => (
              <option key={tenant.tenant_id} value={tenant.tenant_id}>
                {tenant.tenant_id} ({tenant.name})
              </option>
            ))}
          </select>
        </div>

        <p className="mt-3 text-sm text-muted-foreground">
          Signed-in tenant: <span className="font-semibold text-foreground">{tenantLabel}</span>
        </p>

        {tenantOptionsLoading && (
          <p className="mt-2 text-xs text-muted-foreground">Loading tenant options...</p>
        )}

        {isTenantMismatch && (
          <div className="mt-2 space-y-2 text-xs text-amber-700">
            <p>
              You selected <span className="font-semibold">{selectedTenantViewId}</span>, but your current session is
              tenant <span className="font-semibold">{activeTenantId}</span>. Sign in with the selected tenant to
              manage its documents.
            </p>
            <a href={selectedTenantLoginHref} className="inline-flex underline underline-offset-2">
              Open login with selected tenant
            </a>
          </div>
        )}
      </section>

      <section className="rounded-lg border bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold">Upload Document</h2>
        <p className="mt-1 text-xs text-muted-foreground">
          Uploaded files are added only to tenant <span className="font-semibold text-foreground">{tenantLabel}</span>.
        </p>

        <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center">
          <Input
            id="doc-upload-input"
            type="file"
            onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
          />
          <Button type="button" onClick={onUpload} disabled={isUploading || !selectedFile || isTenantMismatch}>
            {isUploading ? "Uploading..." : "Upload"}
          </Button>
        </div>
      </section>

      <section className="rounded-lg border bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold">Tenant Document Library</h2>
        <p className="mt-1 text-xs text-muted-foreground">
          Tenant <span className="font-semibold text-foreground">{tenantLabel}</span> currently has {documents.length} document(s).
        </p>

        <div className="mt-4 overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b text-left text-xs uppercase tracking-wide text-muted-foreground">
                <th className="py-2 pr-4">Document ID</th>
                <th className="py-2 pr-4">Filename</th>
                <th className="py-2 pr-4">Status</th>
                <th className="py-2 pr-4">Actions</th>
              </tr>
            </thead>
            <tbody>
              {!isLoading && documents.length === 0 && (
                <tr>
                  <td colSpan={4} className="py-6 text-center text-sm text-muted-foreground">
                    No documents found for this tenant.
                  </td>
                </tr>
              )}

              {documents.map((doc) => (
                <tr key={doc.document_id} className="border-b hover:bg-gray-50">
                  <td className="py-2 pr-4 font-mono text-xs">{doc.document_id}</td>
                  <td className="py-2 pr-4">{doc.filename}</td>
                  <td className="py-2 pr-4">
                    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${statusClass(doc.status)}`}>
                      {doc.status}
                    </span>
                  </td>
                  <td className="py-2 pr-4">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => void onDelete(doc.document_id)}
                      disabled={deletingId === doc.document_id}
                    >
                      {deletingId === doc.document_id ? "Deleting..." : "Delete"}
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
