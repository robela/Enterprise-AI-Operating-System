import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Eye, Pencil, Plus, RefreshCw } from "lucide-react";
import type { TenantDocument } from "../types";

function statusClass(status: TenantDocument["status"]): string {
  if (status === "indexed") return "bg-emerald-100 text-emerald-700";
  if (status === "processing") return "bg-amber-100 text-amber-700";
  if (status === "failed") return "bg-rose-100 text-rose-700";
  return "bg-slate-100 text-slate-700";
}

function statusDotClass(status: TenantDocument["status"]): string {
  if (status === "indexed") return "bg-emerald-500";
  if (status === "processing") return "bg-sky-500";
  if (status === "failed") return "bg-rose-500";
  return "bg-amber-500";
}

type Props = {
  documents: TenantDocument[];
  filteredDocuments: TenantDocument[];
  tenantName: string;
  searchQuery: string;
  isLoading: boolean;
  onSearchChange: (value: string) => void;
  onRefresh: () => void;
  onOpenAddDocument: () => void;
  onView: (documentId: string) => void;
  onEdit: (documentId: string) => void;
};

export function DocumentTable({
  documents,
  filteredDocuments,
  tenantName,
  searchQuery,
  isLoading,
  onSearchChange,
  onRefresh,
  onOpenAddDocument,
  onView,
  onEdit,
}: Props) {
  return (
    <TooltipProvider>
      <section className="rounded-lg border bg-white p-3 shadow-sm sm:p-5">
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <Input
          type="text"
          placeholder="Search filename..."
          className="w-full sm:max-w-xs"
          value={searchQuery}
          onChange={(event) => onSearchChange(event.target.value)}
        />

        <div className="flex items-center justify-end gap-2">
          <span className="hidden text-xs text-muted-foreground sm:inline">
            Showing {filteredDocuments.length} of {documents.length}
          </span>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                type="button"
                variant="outline"
                size="icon"
                aria-label={isLoading ? "Refreshing documents" : "Refresh documents"}
                onClick={onRefresh}
                disabled={isLoading}
              >
                <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
              </Button>
            </TooltipTrigger>
            <TooltipContent>{isLoading ? "Refreshing documents" : "Refresh documents"}</TooltipContent>
          </Tooltip>
          <Button type="button" onClick={onOpenAddDocument} className="gap-1.5">
            <Plus className="h-4 w-4" />
            Add
          </Button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b text-left text-xs uppercase tracking-wide text-muted-foreground">
              <th className="py-2 pr-4">Filename</th>
              <th className="py-2 pr-4">Tenant</th>
              <th className="py-2 pr-4">Type</th>
              <th className="py-2 pr-4">Ingestion Status</th>
              <th className="py-2 pr-1 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {!isLoading && filteredDocuments.length === 0 && (
              <tr>
                <td colSpan={5} className="py-6 text-center text-sm text-muted-foreground">
                  No documents found.
                </td>
              </tr>
            )}

            {filteredDocuments.map((doc) => (
              <tr key={doc.document_id} className="border-b hover:bg-gray-50">
                <td className="max-w-sm py-2 pr-4">{doc.filename}</td>
                <td className="py-2 pr-4 text-sm">{tenantName}</td>
                <td className="py-2 pr-4">
                  <span className="inline-flex rounded-full border border-slate-200 px-2 py-0.5 text-xs">
                    {(doc.doc_type || "other").toUpperCase()}
                  </span>
                </td>
                <td className="py-2 pr-4">
                  <div className="flex items-center gap-2">
                    <span className={`h-2.5 w-2.5 rounded-full ${statusDotClass(doc.status)}`} />
                    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${statusClass(doc.status)}`}>
                      {doc.status.toUpperCase()}
                    </span>
                  </div>
                </td>
                <td className="py-2 pr-1">
                  <div className="flex items-center justify-end gap-1">
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          type="button"
                          variant="secondary"
                          size="icon"
                          aria-label="View"
                          onClick={() => onView(doc.document_id)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>View document</TooltipContent>
                    </Tooltip>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          type="button"
                          variant="outline"
                          size="icon"
                          aria-label="Edit"
                          onClick={() => onEdit(doc.document_id)}
                        >
                          <Pencil className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Edit document</TooltipContent>
                    </Tooltip>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      </section>
    </TooltipProvider>
  );
}
