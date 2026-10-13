"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AxiosError } from "axios";
import { Check, FileText, Image, ListChecks, Text, X } from "lucide-react";
import { toast } from "sonner";

import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { apiClient } from "@/services/api/client";
import {
  documentService,
  type DocumentChunkPreview,
  type ExtractedWorkflow,
} from "@/services/api/documents";
import { Button } from "@/components/ui/button";
import type { DocumentTypeValue, LifecycleStatus } from "@/types/document";
import { useAuth } from "@/utils/auth";
import { AddDocumentSidebarContent } from "./components/AddDocumentSidebarContent";
import { DocumentTable } from "./components/DocumentTable";
import { EditDocumentSidebarContent } from "./components/EditDocumentSidebarContent";
import { PdfPreview } from "./components/PdfPreview";
import type { TenantDocument, TenantListItem } from "./types";

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

export default function DocumentsPage() {
  const { tenant_id, role } = useAuth();

  const [documents, setDocuments] = useState<TenantDocument[]>([]);
  const [tenantOptions, setTenantOptions] = useState<TenantListItem[]>([]);
  const [tenantOptionsLoading, setTenantOptionsLoading] = useState(false);

  const [showAddDocSidebar, setShowAddDocSidebar] = useState(false);
  const [uploadTenantId, setUploadTenantId] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadDocumentType, setUploadDocumentType] = useState<DocumentTypeValue | "">("");
  const [uploadLifecycleStatus, setUploadLifecycleStatus] = useState<LifecycleStatus>("active");
  const [showViewDocSidebar, setShowViewDocSidebar] = useState(false);
  const [viewDocumentId, setViewDocumentId] = useState<string | null>(null);
  const [viewTab, setViewTab] = useState<"preview" | "chunks" | "images" | "details" | "extracted">("preview");
  const [documentChunks, setDocumentChunks] = useState<DocumentChunkPreview[]>([]);
  const [isChunksLoading, setIsChunksLoading] = useState(false);
  const [chunksError, setChunksError] = useState<string | null>(null);
  const [previewFile, setPreviewFile] = useState<Blob | null>(null);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  const [pageCount, setPageCount] = useState<number | null>(null);
  const [extractedWorkflows, setExtractedWorkflows] = useState<ExtractedWorkflow[]>([]);
  const [isWorkflowsLoading, setIsWorkflowsLoading] = useState(false);
  const [isExtractingWorkflows, setIsExtractingWorkflows] = useState(false);
  const [workflowError, setWorkflowError] = useState<string | null>(null);
  const [editingWorkflowId, setEditingWorkflowId] = useState<string | null>(null);
  const [workflowName, setWorkflowName] = useState("");
  const [workflowSteps, setWorkflowSteps] = useState("");
  const [workflowFields, setWorkflowFields] = useState("");
  const [showEditDocSidebar, setShowEditDocSidebar] = useState(false);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
  const [isDeactivating, setIsDeactivating] = useState(false);

  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const tenantLabel = useMemo(() => tenant_id || "unknown", [tenant_id]);
  const activeTenantId = tenant_id ?? "";
  const tenantName = useMemo(
    () => tenantOptions.find((tenant) => tenant.tenant_id === activeTenantId)?.name || tenantLabel,
    [activeTenantId, tenantLabel, tenantOptions],
  );

  const filteredDocuments = useMemo(() => {
    const term = searchQuery.trim().toLowerCase();
    if (!term) {
      return documents;
    }
    return documents.filter((doc) => doc.filename.toLowerCase().includes(term));
  }, [documents, searchQuery]);

  const selectedDocument = useMemo(
    () => documents.find((doc) => doc.document_id === selectedDocumentId) ?? null,
    [documents, selectedDocumentId],
  );

  const viewedDocument = useMemo(
    () => documents.find((doc) => doc.document_id === viewDocumentId) ?? null,
    [documents, viewDocumentId],
  );

  const activeCount = useMemo(
    () => documents.filter((doc) => doc.status === "indexed" && (doc.lifecycle_status ?? "active") === "active").length,
    [documents],
  );

  const inactiveCount = useMemo(
    () => documents.filter((doc) => (doc.lifecycle_status ?? "active") === "inactive").length,
    [documents],
  );

  const ingestingCount = useMemo(
    () => documents.filter((doc) => doc.status === "pending" || doc.status === "processing").length,
    [documents],
  );

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
    } catch {
      if (activeTenantId) {
        setTenantOptions([{ tenant_id: activeTenantId, name: activeTenantId, is_active: true }]);
      } else {
        setTenantOptions([]);
      }
    } finally {
      setTenantOptionsLoading(false);
    }
  }, [activeTenantId]);

  const fetchDocuments = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await documentService.getList();
      setDocuments(data);
    } catch (error) {
      toast.error(getErrorMessage(error, "Failed to load tenant documents"));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadTenantOptions();
  }, [loadTenantOptions]);

  useEffect(() => {
    void fetchDocuments();
  }, [fetchDocuments]);

  useEffect(() => {
    if (!showViewDocSidebar || !viewedDocument?.filename.toLowerCase().endsWith(".pdf")) {
      return;
    }

    let cancelled = false;
    setIsPreviewLoading(true);
    setPreviewError(null);
    setPreviewFile(null);

    void documentService.getContent(viewedDocument.document_id)
      .then((file) => {
        if (cancelled) return;
        setPreviewFile(new Blob([file], { type: "application/pdf" }));
      })
      .catch(() => {
        if (!cancelled) setPreviewError("Unable to load the PDF preview.");
      })
      .finally(() => {
        if (!cancelled) setIsPreviewLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [showViewDocSidebar, viewedDocument]);

  useEffect(() => {
    if (!showViewDocSidebar || !viewedDocument?.filename.toLowerCase().endsWith(".pdf")) {
      setPageCount(null);
      return;
    }

    let cancelled = false;
    void documentService.getPageCount(viewedDocument.document_id)
      .then((count) => {
        if (!cancelled) setPageCount(count);
      })
      .catch(() => {
        if (!cancelled) setPageCount(null);
      });

    return () => {
      cancelled = true;
    };
  }, [showViewDocSidebar, viewedDocument]);

  useEffect(() => {
    if (!showViewDocSidebar || viewTab !== "chunks" || !viewedDocument) return;

    let cancelled = false;
    setIsChunksLoading(true);
    setChunksError(null);
    void documentService.getChunks(viewedDocument.document_id)
      .then((chunks) => {
        if (!cancelled) setDocumentChunks(chunks);
      })
      .catch(() => {
        if (!cancelled) setChunksError("Unable to load indexed document chunks.");
      })
      .finally(() => {
        if (!cancelled) setIsChunksLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [showViewDocSidebar, viewTab, viewedDocument]);

  const loadExtractedWorkflows = useCallback(async (documentId: string) => {
    setIsWorkflowsLoading(true);
    setWorkflowError(null);
    try {
      setExtractedWorkflows(await documentService.getExtractedWorkflows(documentId));
    } catch (error) {
      setWorkflowError(getErrorMessage(error, "Unable to load extracted workflows."));
    } finally {
      setIsWorkflowsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!showViewDocSidebar || viewTab !== "extracted" || !viewedDocument) return;
    void loadExtractedWorkflows(viewedDocument.document_id);
  }, [loadExtractedWorkflows, showViewDocSidebar, viewTab, viewedDocument]);

  const handleAddSidebarChange = (open: boolean) => {
    setShowAddDocSidebar(open);
    if (open && role === "tenant_admin") {
      setUploadTenantId(activeTenantId);
    }
    if (!open) {
      setUploadTenantId("");
      setUploadFile(null);
      setUploadDocumentType("");
      setUploadLifecycleStatus("active");
    }
  };

  const onUpload = async () => {
    if (!uploadTenantId) {
      toast.error("Tenant selection is required");
      return;
    }

    if (!uploadFile) {
      toast.error("Choose a file to upload");
      return;
    }

    if (!uploadDocumentType) {
      toast.error("Document type is required");
      return;
    }

    if (!activeTenantId) {
      toast.error("No active tenant in session");
      return;
    }

    if (uploadTenantId !== activeTenantId) {
      toast.error("Selected tenant does not match your signed-in tenant");
      return;
    }

    setIsUploading(true);
    try {
      await documentService.upload(uploadFile, {
        document_type: uploadDocumentType,
        lifecycle_status: uploadLifecycleStatus,
      });
      toast.success("File uploaded!", {
        description: `${uploadFile.name} has been uploaded successfully and is being processed.`,
      });

      setUploadFile(null);
      await fetchDocuments();
      setShowAddDocSidebar(false);
    } catch (error) {
      toast.error(getErrorMessage(error, "Upload failed"));
    } finally {
      setIsUploading(false);
    }
  };

  const handleEditSidebarChange = (open: boolean) => {
    setShowEditDocSidebar(open);
    if (!open) {
      setSelectedDocumentId(null);
    }
  };

  const handleViewSidebarChange = (open: boolean) => {
    setShowViewDocSidebar(open);
    if (!open) {
      setViewDocumentId(null);
      setViewTab("preview");
      setDocumentChunks([]);
      setChunksError(null);
      setPageCount(null);
      setExtractedWorkflows([]);
      setWorkflowError(null);
      setEditingWorkflowId(null);
    }
  };

  const onDeactivateDocument = async () => {
    if (!selectedDocumentId) {
      return;
    }

    setIsDeactivating(true);
    try {
      await documentService.setLifecycleStatus(selectedDocumentId, "inactive");
      setDocuments((prev) =>
        prev.map((doc) =>
          doc.document_id === selectedDocumentId
            ? { ...doc, lifecycle_status: "inactive" }
            : doc,
        ),
      );
      toast.success("Document deactivated");
      setShowEditDocSidebar(false);
      setSelectedDocumentId(null);
      await fetchDocuments();
    } catch (error) {
      toast.error(getErrorMessage(error, "Deactivate failed"));
    } finally {
      setIsDeactivating(false);
    }
  };

  const onExtractWorkflows = async () => {
    if (!viewedDocument) return;
    setIsExtractingWorkflows(true);
    setWorkflowError(null);
    try {
      const workflows = await documentService.extractWorkflows(viewedDocument.document_id);
      setExtractedWorkflows(workflows);
      toast.success(`${workflows.length} workflow drafts extracted`);
    } catch (error) {
      setWorkflowError(getErrorMessage(error, "Workflow extraction failed."));
    } finally {
      setIsExtractingWorkflows(false);
    }
  };

  const beginWorkflowEdit = (workflow: ExtractedWorkflow) => {
    setEditingWorkflowId(workflow.workflow_id);
    setWorkflowName(workflow.name);
    setWorkflowSteps(workflow.steps.join("\n"));
    setWorkflowFields(workflow.required_fields.join(", "));
  };

  const onSaveWorkflow = async () => {
    if (!editingWorkflowId) return;
    try {
      const updated = await documentService.updateExtractedWorkflow(editingWorkflowId, {
        name: workflowName.trim(),
        steps: workflowSteps.split("\n").map((step) => step.trim()).filter(Boolean),
        required_fields: workflowFields.split(",").map((field) => field.trim()).filter(Boolean),
      });
      setExtractedWorkflows((workflows) => workflows.map((workflow) =>
        workflow.workflow_id === updated.workflow_id ? updated : workflow,
      ));
      setEditingWorkflowId(null);
      toast.success("Workflow draft saved");
    } catch (error) {
      toast.error(getErrorMessage(error, "Unable to save workflow draft"));
    }
  };

  const onReviewWorkflow = async (workflowId: string, action: "approve" | "reject") => {
    try {
      const updated = await documentService.reviewExtractedWorkflow(workflowId, action);
      setExtractedWorkflows((workflows) => workflows.map((workflow) =>
        workflow.workflow_id === updated.workflow_id ? updated : workflow,
      ));
      toast.success(action === "approve" ? "Workflow approved" : "Workflow rejected");
    } catch (error) {
      toast.error(getErrorMessage(error, "Unable to review workflow"));
    }
  };

  return (
    <div className="mx-6 flex h-full flex-col overflow-y-auto">
      <h1 className="mt-5 mb-2 scroll-m-20 text-3xl font-bold tracking-tight">Manage Documents</h1>
      <p className="mb-1 text-sm text-gray-500">
        On this page, you can see the list of documents. You can add new documents and replace existing files.
      </p>
      <p className="mb-6 text-xs text-muted-foreground">
        Active tenant: <span className="font-semibold text-foreground">{tenantLabel}</span>
      </p>

      <div className="mb-6 flex flex-wrap items-center justify-between gap-3 text-sm text-muted-foreground">
        <div>
          There are <span className="font-bold text-emerald-600">{activeCount}</span> active and{" "}
          <span className="font-bold">{inactiveCount}</span> inactive documents.
        </div>
        {ingestingCount > 0 && (
          <div className="flex items-center">
            <span className="relative flex h-3 w-3">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-sky-400 opacity-75" />
              <span className="relative inline-flex h-3 w-3 rounded-full bg-sky-500" />
            </span>
            <span className="ml-2 text-sky-600">
              {ingestingCount} {ingestingCount === 1 ? "document" : "documents"} currently ingesting.
            </span>
          </div>
        )}
      </div>

      <DocumentTable
        documents={documents}
        filteredDocuments={filteredDocuments}
        tenantName={tenantName}
        searchQuery={searchQuery}
        isLoading={isLoading}
        onSearchChange={setSearchQuery}
        onRefresh={() => void fetchDocuments()}
        onOpenAddDocument={() => setShowAddDocSidebar(true)}
        onView={(documentId) => {
          setViewDocumentId(documentId);
          setViewTab("preview");
          setShowViewDocSidebar(true);
        }}
        onEdit={(documentId) => {
          setSelectedDocumentId(documentId);
          setShowEditDocSidebar(true);
        }}
      />

      <Sheet open={showViewDocSidebar} onOpenChange={handleViewSidebarChange}>
        <SheetContent side="right" className="flex h-full !w-full flex-col overflow-hidden sm:!w-[70vw] sm:!max-w-none">
          <SheetHeader>
            <SheetTitle>View Document</SheetTitle>
            <SheetDescription>
              Review document details.
            </SheetDescription>
          </SheetHeader>

          {viewedDocument && (
            <div className="mt-6 flex min-h-0 flex-1 flex-col overflow-hidden">
              <TooltipProvider>
              <div role="tablist" aria-label="Document view" className="flex shrink-0 gap-1 border-b">
                {viewedDocument.filename.toLowerCase().endsWith(".pdf") && (
                  <button
                    type="button"
                    role="tab"
                    aria-selected={viewTab === "preview"}
                    className={`border-b-2 px-3 py-2 text-sm font-medium transition-colors ${viewTab === "preview" ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"}`}
                    onClick={() => setViewTab("preview")}
                  >
                    <span className="inline-flex items-center gap-1.5"><FileText className="h-4 w-4" />PDF</span>
                  </button>
                )}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button type="button" role="tab" aria-label="Document details" aria-selected={viewTab === "details"} className={`border-b-2 px-3 py-2 text-sm font-medium transition-colors ${viewTab === "details" ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"}`} onClick={() => setViewTab("details")}>
                      <span className="inline-flex items-center gap-1.5"><FileText className="h-4 w-4" />Details</span>
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>Details</TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button type="button" role="tab" aria-label="Preview chunks" aria-selected={viewTab === "chunks"} className={`border-b-2 px-3 py-2 text-sm font-medium transition-colors ${viewTab === "chunks" ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"}`} onClick={() => setViewTab("chunks")}>
                      <span className="inline-flex items-center gap-1.5"><Text className="h-4 w-4" />Chunks</span>
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>Preview chunks</TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button type="button" role="tab" aria-label="Preview images" aria-selected={viewTab === "images"} className={`border-b-2 px-3 py-2 text-sm font-medium transition-colors ${viewTab === "images" ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"}`} onClick={() => setViewTab("images")}>
                      <span className="inline-flex items-center gap-1.5"><Image className="h-4 w-4" />Images</span>
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>Preview images</TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button type="button" role="tab" aria-label="Extracted workflows" aria-selected={viewTab === "extracted"} className={`border-b-2 px-3 py-2 text-sm font-medium transition-colors ${viewTab === "extracted" ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"}`} onClick={() => setViewTab("extracted")}>
                      <span className="inline-flex items-center gap-1.5"><ListChecks className="h-4 w-4" />Extracted</span>
                    </button>
                  </TooltipTrigger>
                  <TooltipContent>Review extracted workflows</TooltipContent>
                </Tooltip>
              </div>
              </TooltipProvider>

              {viewTab === "preview" && viewedDocument.filename.toLowerCase().endsWith(".pdf") && (
                <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-md border bg-slate-50">
                  {isPreviewLoading && (
                    <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                      Loading PDF preview...
                    </div>
                  )}
                  {previewError && (
                    <div className="flex h-full items-center justify-center p-4 text-center text-sm text-destructive">
                      {previewError}
                    </div>
                  )}
                  {previewFile && !isPreviewLoading && !previewError && (
                    <PdfPreview file={previewFile} />
                  )}
                </div>
              )}

              {viewTab === "details" && (
                <div role="tabpanel" className="space-y-5 overflow-y-auto py-5">
                  <div className="rounded-md border bg-slate-50 p-4 text-sm">
                    <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Document</p>
                    <p className="mt-1 font-medium text-slate-900">{viewedDocument.filename}</p>
                  </div>
                  <div className="grid grid-cols-1 gap-3 rounded-md border p-4 text-sm md:grid-cols-2 xl:grid-cols-4">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Type</p>
                      <p className="mt-1 font-medium">{(viewedDocument.doc_type ?? "other").toUpperCase()}</p>
                    </div>
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Status</p>
                      <p className="mt-1 font-medium">{viewedDocument.status.toUpperCase()}</p>
                    </div>
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Tenant</p>
                      <p className="mt-1 font-medium">{tenantName}</p>
                    </div>
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Pages</p>
                      <p className="mt-1 font-medium">{pageCount ?? (viewedDocument.filename.toLowerCase().endsWith(".pdf") ? "Loading..." : "-" )}</p>
                    </div>
                  </div>
                </div>
              )}

              {viewTab === "chunks" && (
                <div role="tabpanel" className="min-h-0 flex-1 overflow-y-auto py-5">
                  {isChunksLoading && <p className="text-sm text-muted-foreground">Loading indexed chunks...</p>}
                  {chunksError && <p className="text-sm text-destructive">{chunksError}</p>}
                  {!isChunksLoading && !chunksError && documentChunks.length === 0 && (
                    <p className="text-sm text-muted-foreground">No indexed chunks are available for this document.</p>
                  )}
                  <div className="space-y-3">
                    {documentChunks.map((chunk) => (
                      <article key={chunk.index} className="rounded-md border p-4 text-sm">
                        <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">Chunk {chunk.index + 1}</p>
                        <p className="whitespace-pre-wrap text-foreground">{chunk.text}</p>
                      </article>
                    ))}
                  </div>
                </div>
              )}

              {viewTab === "images" && (
                <div role="tabpanel" className="flex min-h-0 flex-1 items-center justify-center py-5 text-center text-sm text-muted-foreground">
                  No extracted images are available for this document.
                </div>
              )}

              {viewTab === "extracted" && (
                <div role="tabpanel" className="min-h-0 flex-1 overflow-y-auto py-5">
                  <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                    <p className="text-sm text-muted-foreground">Drafts are extracted from explicit PDF instructions and require review before use.</p>
                    <Button size="sm" onClick={() => void onExtractWorkflows()} disabled={isExtractingWorkflows || !viewedDocument.filename.toLowerCase().endsWith(".pdf")}>
                      <ListChecks className="mr-2 h-4 w-4" />{isExtractingWorkflows ? "Extracting..." : "Extract"}
                    </Button>
                  </div>
                  {workflowError && <p className="mb-4 text-sm text-destructive">{workflowError}</p>}
                  {isWorkflowsLoading && <p className="text-sm text-muted-foreground">Loading extracted workflows...</p>}
                  {!isWorkflowsLoading && !workflowError && extractedWorkflows.length === 0 && (
                    <p className="text-sm text-muted-foreground">No workflow drafts exist yet. Select Extract to create reviewable drafts from this PDF.</p>
                  )}
                  <div className="space-y-3">
                    {extractedWorkflows.map((workflow) => (
                      <article key={workflow.workflow_id} className="rounded-md border p-4 text-sm">
                        {editingWorkflowId === workflow.workflow_id ? (
                          <div className="space-y-3">
                            <input aria-label="Workflow name" value={workflowName} onChange={(event) => setWorkflowName(event.target.value)} className="h-9 w-full rounded-md border px-3" />
                            <textarea aria-label="Workflow steps" value={workflowSteps} onChange={(event) => setWorkflowSteps(event.target.value)} className="min-h-28 w-full rounded-md border p-3" />
                            <input aria-label="Required fields" value={workflowFields} onChange={(event) => setWorkflowFields(event.target.value)} className="h-9 w-full rounded-md border px-3" placeholder="field_one, field_two" />
                            <div className="flex gap-2"><Button size="sm" onClick={() => void onSaveWorkflow()}>Save draft</Button><Button size="sm" variant="outline" onClick={() => setEditingWorkflowId(null)}>Cancel</Button></div>
                          </div>
                        ) : (
                          <>
                            <div className="flex flex-wrap items-start justify-between gap-3">
                              <div><h3 className="font-semibold text-foreground">{workflow.name}</h3><p className="mt-1 text-xs text-muted-foreground">Pages {workflow.source_pages.join(", ")} · {workflow.confidence} confidence · {workflow.status}</p></div>
                              <div className="flex gap-2"><Button size="sm" variant="outline" onClick={() => beginWorkflowEdit(workflow)}>Edit</Button>{workflow.status === "draft" && <><Button size="icon" aria-label="Approve workflow" title="Approve workflow" onClick={() => void onReviewWorkflow(workflow.workflow_id, "approve")}><Check className="h-4 w-4" /></Button><Button size="icon" variant="destructive" aria-label="Reject workflow" title="Reject workflow" onClick={() => void onReviewWorkflow(workflow.workflow_id, "reject")}><X className="h-4 w-4" /></Button></>}</div>
                            </div>
                            <ol className="mt-3 list-decimal space-y-1 pl-5 text-foreground">{workflow.steps.map((step, index) => <li key={`${workflow.workflow_id}-${index}`}>{step}</li>)}</ol>
                            <p className="mt-3 text-xs text-muted-foreground">Required fields: {workflow.required_fields.length ? workflow.required_fields.join(", ") : "Set during review"}</p>
                            <p className="mt-2 whitespace-pre-wrap border-l-2 pl-3 text-xs text-muted-foreground">{workflow.source_excerpt}</p>
                          </>
                        )}
                      </article>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </SheetContent>
      </Sheet>

      <Sheet open={showAddDocSidebar} onOpenChange={handleAddSidebarChange}>
        <SheetContent side="right" className="w-full overflow-y-auto sm:max-w-4xl">
          <SheetHeader>
            <SheetTitle>Add Document</SheetTitle>
            <SheetDescription>
              Select a document that the AI can use. Tenant selection is required before upload.
            </SheetDescription>
          </SheetHeader>

          <AddDocumentSidebarContent
            tenantOptions={tenantOptions}
            tenantOptionsLoading={tenantOptionsLoading}
            activeTenantId={activeTenantId}
            uploadTenantId={uploadTenantId}
            lockTenantSelection={role === "tenant_admin"}
            uploadFile={uploadFile}
            documentType={uploadDocumentType}
            lifecycleStatus={uploadLifecycleStatus}
            isUploading={isUploading}
            onUploadTenantChange={setUploadTenantId}
            onUploadFileChange={setUploadFile}
            onDocumentTypeChange={setUploadDocumentType}
            onLifecycleStatusChange={setUploadLifecycleStatus}
            onUpload={() => void onUpload()}
            onCancel={() => setShowAddDocSidebar(false)}
          />
        </SheetContent>
      </Sheet>

      <Sheet open={showEditDocSidebar} onOpenChange={handleEditSidebarChange}>
        <SheetContent side="right" className="w-full overflow-y-auto sm:max-w-xl">
          <SheetHeader>
            <SheetTitle>Edit Document</SheetTitle>
            <SheetDescription>
              Update document lifecycle controls for the selected file.
            </SheetDescription>
          </SheetHeader>

          {selectedDocument && (
            <EditDocumentSidebarContent
              document={selectedDocument}
              isSaving={isDeactivating}
              onDeactivate={() => void onDeactivateDocument()}
              onCancel={() => setShowEditDocSidebar(false)}
            />
          )}
        </SheetContent>
      </Sheet>
    </div>
  );
}
