import { Button } from "@/components/ui/button";
import { SheetClose, SheetFooter } from "@/components/ui/sheet";
import type { TenantDocument } from "../types";

type Props = {
  document: TenantDocument;
  isSaving: boolean;
  onDeactivate: () => void;
  onCancel: () => void;
};

export function EditDocumentSidebarContent({
  document,
  isSaving,
  onDeactivate,
  onCancel,
}: Props) {
  const lifecycleStatus = (document.lifecycle_status ?? "active").toUpperCase();
  const canDeactivate = (document.lifecycle_status ?? "active") !== "inactive";

  return (
    <div className="mt-6 space-y-5">
      <div className="rounded-md border bg-slate-50 p-4 text-sm">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Document</p>
        <p className="mt-1 font-medium text-slate-900">{document.filename}</p>
        <p className="mt-2 text-xs text-muted-foreground">ID: {document.document_id}</p>
      </div>

      <div className="grid grid-cols-1 gap-3 rounded-md border p-4 text-sm md:grid-cols-2">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Type</p>
          <p className="mt-1 font-medium">{(document.doc_type ?? "other").toUpperCase()}</p>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Lifecycle</p>
          <p className="mt-1 font-medium">{lifecycleStatus}</p>
        </div>
      </div>

      <p className="text-xs text-muted-foreground">
        Deactivating a document keeps it stored but excludes it from active document usage.
      </p>

      <SheetFooter className="pt-2">
        <SheetClose asChild>
          <Button type="button" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        </SheetClose>
        <Button
          type="button"
          variant="destructive"
          onClick={onDeactivate}
          disabled={isSaving || !canDeactivate}
        >
          {isSaving ? "Deactivating..." : canDeactivate ? "Deactivate Document" : "Already Inactive"}
        </Button>
      </SheetFooter>
    </div>
  );
}
