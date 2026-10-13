import { useMemo, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { SheetClose, SheetFooter } from "@/components/ui/sheet";
import type { DocumentTypeValue, LifecycleStatus } from "@/types/document";
import type { TenantListItem } from "../types";

type Props = {
  tenantOptions: TenantListItem[];
  tenantOptionsLoading: boolean;
  activeTenantId: string;
  uploadTenantId: string;
  lockTenantSelection: boolean;
  uploadFile: File | null;
  documentType: DocumentTypeValue | "";
  lifecycleStatus: LifecycleStatus;
  isUploading: boolean;
  onUploadTenantChange: (tenantId: string) => void;
  onUploadFileChange: (file: File | null) => void;
  onDocumentTypeChange: (value: DocumentTypeValue | "") => void;
  onLifecycleStatusChange: (value: LifecycleStatus) => void;
  onUpload: () => void;
  onCancel: () => void;
};

export function AddDocumentSidebarContent({
  tenantOptions,
  tenantOptionsLoading,
  activeTenantId,
  uploadTenantId,
  lockTenantSelection,
  uploadFile,
  documentType,
  lifecycleStatus,
  isUploading,
  onUploadTenantChange,
  onUploadFileChange,
  onDocumentTypeChange,
  onLifecycleStatusChange,
  onUpload,
  onCancel,
}: Props) {
  const uploadInputRef = useRef<HTMLInputElement | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);

  const isTenantMismatch = Boolean(
    uploadTenantId && activeTenantId && uploadTenantId !== activeTenantId,
  );

  const selectedTenantLoginHref = useMemo(() => {
    if (!uploadTenantId) {
      return "/login";
    }
    return `/login?tenant=${encodeURIComponent(uploadTenantId)}`;
  }, [uploadTenantId]);

  return (
    <form className="mt-6 space-y-4" onSubmit={(event) => event.preventDefault()}>
      <div className="space-y-1">
        <label htmlFor="upload-tenant-select" className="text-sm font-medium">
          Tenant <span className="text-rose-600">*</span>
        </label>
        {lockTenantSelection ? (
          <p className="rounded-md border bg-muted px-3 py-2 text-sm">{activeTenantId}</p>
        ) : (
          <select
            id="upload-tenant-select"
            className="w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            value={uploadTenantId}
            onChange={(event) => onUploadTenantChange(event.target.value)}
            required
          >
            <option value="">Select tenant</option>
            {tenantOptions.map((tenant) => (
              <option key={tenant.tenant_id} value={tenant.tenant_id}>
                {tenant.tenant_id} ({tenant.name})
              </option>
            ))}
          </select>
        )}
        {!lockTenantSelection && tenantOptionsLoading && <p className="text-xs text-muted-foreground">Loading tenants...</p>}
      </div>

      {isTenantMismatch && (
        <div className="space-y-2 text-xs text-amber-700">
          <p>
            You selected <span className="font-semibold">{uploadTenantId}</span>, but your current session is tenant{" "}
            <span className="font-semibold">{activeTenantId}</span>. Sign in with the selected tenant to upload for that tenant.
          </p>
          <a href={selectedTenantLoginHref} className="inline-flex underline underline-offset-2">
            Open login with selected tenant
          </a>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="space-y-1">
          <label htmlFor="upload-document-type" className="text-sm font-medium">
            Type <span className="text-rose-600">*</span>
          </label>
          <select
            id="upload-document-type"
            className="w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            value={documentType}
            onChange={(event) => onDocumentTypeChange(event.target.value as DocumentTypeValue | "")}
            required
          >
            <option value="">Select type</option>
            <option value="primary">Basic</option>
            <option value="secondary">Reference</option>
            <option value="pdf">PDF</option>
            <option value="word">Word</option>
            <option value="excel">Excel</option>
            <option value="text">Text</option>
            <option value="markdown">Markdown</option>
            <option value="html">HTML</option>
            <option value="other">Other</option>
          </select>
        </div>

        <div className="space-y-1">
          <label htmlFor="upload-lifecycle-status" className="text-sm font-medium">
            Status
          </label>
          <select
            id="upload-lifecycle-status"
            className="w-full rounded-md border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            value={lifecycleStatus}
            onChange={(event) => onLifecycleStatusChange(event.target.value as LifecycleStatus)}
          >
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
      </div>

      <div className="space-y-2">
        <label htmlFor="doc-upload-input-sidebar" className="text-sm font-medium">
          File <span className="text-rose-600">*</span>
        </label>
        <input
          id="doc-upload-input-sidebar"
          ref={uploadInputRef}
          type="file"
          className="hidden"
          onChange={(event) => onUploadFileChange(event.target.files?.[0] ?? null)}
        />

        {!uploadFile && (
          <button
            type="button"
            className={`flex min-h-48 w-full items-center justify-center rounded-lg border border-dashed p-6 text-center transition ${
              isDragActive ? "border-sky-500 bg-sky-50" : "border-slate-300 bg-slate-50"
            }`}
            onClick={() => uploadInputRef.current?.click()}
            onDragOver={(event) => {
              event.preventDefault();
              setIsDragActive(true);
            }}
            onDragLeave={() => setIsDragActive(false)}
            onDrop={(event) => {
              event.preventDefault();
              setIsDragActive(false);
              onUploadFileChange(event.dataTransfer.files?.[0] ?? null);
            }}
          >
            <span className="text-sm text-muted-foreground">
              {isDragActive ? "Drop the file here" : "Drag and drop a file here, or click to browse"}
            </span>
          </button>
        )}

        {uploadFile && (
          <div className="rounded-md border bg-slate-50 p-3">
            <p className="text-xs font-semibold text-slate-700">Selected file</p>
            <p className="mt-1 text-sm text-slate-900">{uploadFile.name}</p>
            <p className="text-xs text-muted-foreground">{(uploadFile.size / 1024).toFixed(1)} KB</p>
          </div>
        )}
      </div>

      <SheetFooter className="pt-2">
        <SheetClose asChild>
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        </SheetClose>
        <Button
          type="button"
          variant="outline"
          disabled={isUploading || !uploadFile}
          onClick={() => {
            onUploadFileChange(null);
            setIsDragActive(false);
            if (uploadInputRef.current) {
              uploadInputRef.current.value = "";
            }
          }}
        >
          Deselect
        </Button>
        <Button
          type="button"
          onClick={onUpload}
          disabled={isUploading || !uploadFile || !uploadTenantId || !documentType || isTenantMismatch}
        >
          {isUploading ? "Uploading..." : "Upload"}
        </Button>
      </SheetFooter>
    </form>
  );
}
