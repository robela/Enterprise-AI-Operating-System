import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, jest } from "@jest/globals";

import DocumentsPage from "./page";
import { apiClient } from "@/services/api/client";
import { documentService } from "@/services/api/documents";

const mockApiGet = apiClient.get as unknown as jest.MockedFunction<any>;
const mockDocumentUpload = documentService.upload as unknown as jest.MockedFunction<any>;
const mockDocumentGetList = documentService.getList as unknown as jest.MockedFunction<any>;
const mockDocumentSetLifecycleStatus = documentService.setLifecycleStatus as unknown as jest.MockedFunction<any>;

jest.mock("@/services/api/client", () => ({
  apiClient: {
    get: jest.fn(),
    delete: jest.fn(),
  },
}));

jest.mock("@/services/api/documents", () => ({
  documentService: {
    getList: jest.fn(),
    upload: jest.fn(),
    update: jest.fn(),
    delete: jest.fn(),
    setLifecycleStatus: jest.fn(),
  },
}));

jest.mock("@/utils/auth", () => ({
  useAuth: () => ({
    tenant_id: "tenant-alpha",
  }),
}));

jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
  },
}));

describe("DocumentsPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockApiGet.mockResolvedValue({
      data: [{ tenant_id: "tenant-alpha", name: "Tenant Alpha", is_active: true }],
    });
    mockDocumentUpload.mockResolvedValue({
      document_id: "doc-uploaded",
      status: "pending",
      chunk_count: 0,
      doc_type: "primary",
      lifecycle_status: "active",
    });
    mockDocumentSetLifecycleStatus.mockResolvedValue({
      document_id: "doc-1",
      status: "indexed",
      chunk_count: 1,
      doc_type: "primary",
      lifecycle_status: "inactive",
    });
  });

  it("shows ingestion indicator when pending documents exist", async () => {
    mockDocumentGetList.mockResolvedValue([
      { document_id: "doc-1", filename: "ready.pdf", status: "indexed", doc_type: "primary", lifecycle_status: "active" },
      { document_id: "doc-2", filename: "ingesting.pdf", status: "pending", doc_type: "secondary", lifecycle_status: "active" },
    ]);

    render(<DocumentsPage />);

    await waitFor(() => {
      expect(screen.queryByText(/currently ingesting/i)).not.toBeNull();
    });
  });

  it("uploads from side popup with type and status metadata", async () => {
    mockDocumentGetList.mockResolvedValue([]);

    render(<DocumentsPage />);

    fireEvent.click(await screen.findByRole("button", { name: /^add$/i }));

    fireEvent.change(screen.getByLabelText(/tenant/i), {
      target: { value: "tenant-alpha" },
    });

    fireEvent.change(screen.getByLabelText(/type/i), {
      target: { value: "primary" },
    });

    const file = new File(["hello"], "policy.txt", { type: "text/plain" });
    fireEvent.change(screen.getByLabelText(/file/i), {
      target: { files: [file] },
    });

    fireEvent.click(screen.getByRole("button", { name: /upload/i }));

    await waitFor(() => {
      expect(documentService.upload).toHaveBeenCalledTimes(1);
    });

    expect(documentService.upload).toHaveBeenCalledWith(file, {
      document_type: "primary",
      lifecycle_status: "active",
    });
  });

  it("blocks upload when selected tenant mismatches active tenant", async () => {
    mockDocumentGetList.mockResolvedValue([]);
    mockApiGet.mockResolvedValueOnce({
      data: [
        { tenant_id: "tenant-alpha", name: "Tenant Alpha", is_active: true },
        { tenant_id: "tenant-other", name: "Tenant Other", is_active: true },
      ],
    });

    render(<DocumentsPage />);

    fireEvent.click(await screen.findByRole("button", { name: /^add$/i }));

    fireEvent.change(screen.getByLabelText(/tenant/i), {
      target: { value: "tenant-other" },
    });

    fireEvent.change(screen.getByLabelText(/type/i), {
      target: { value: "primary" },
    });

    const file = new File(["hello"], "policy.txt", { type: "text/plain" });
    fireEvent.change(screen.getByLabelText(/file/i), {
      target: { files: [file] },
    });

    await waitFor(() => {
      expect(screen.queryByRole("link", { name: /open login with selected tenant/i })).not.toBeNull();
    });

    expect((screen.getByRole("button", { name: /upload/i }) as HTMLButtonElement).disabled).toBe(true);
  });

  it("shows deactivate action in edit popup and deactivates document", async () => {
    mockDocumentGetList.mockResolvedValue([
      { document_id: "doc-1", filename: "policy.pdf", status: "indexed", doc_type: "primary", lifecycle_status: "active" },
    ]);

    render(<DocumentsPage />);

    fireEvent.click(await screen.findByRole("button", { name: /^edit$/i }));

    const deactivateButton = await screen.findByRole("button", { name: /deactivate document/i });
    fireEvent.click(deactivateButton);

    await waitFor(() => {
      expect(documentService.setLifecycleStatus).toHaveBeenCalledWith("doc-1", "inactive");
    });
  });

  it("shows only view and edit row actions", async () => {
    mockDocumentGetList.mockResolvedValue([
      { document_id: "doc-1", filename: "policy.pdf", status: "indexed", doc_type: "primary", lifecycle_status: "active" },
    ]);

    render(<DocumentsPage />);

    await screen.findByText("policy.pdf");

    expect(screen.queryAllByRole("button", { name: /^view$/i }).length).toBeGreaterThan(0);
    expect(screen.queryAllByRole("button", { name: /^edit$/i }).length).toBeGreaterThan(0);
    expect(screen.queryByRole("button", { name: /remove|delete/i })).toBeNull();
  });
});
