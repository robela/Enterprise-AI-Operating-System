import type { DocumentTypeValue, LifecycleStatus } from "@/types/document";

export type DocumentStatus = "pending" | "processing" | "indexed" | "failed";

export interface TenantDocument {
  document_id: string;
  filename: string;
  status: DocumentStatus;
  doc_type?: DocumentTypeValue;
  lifecycle_status?: LifecycleStatus;
}

export interface TenantListItem {
  tenant_id: string;
  name: string;
  is_active: boolean;
}
