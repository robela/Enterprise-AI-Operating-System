"use client";

import { useCallback, useEffect, useState } from "react";
import { AxiosError } from "axios";
import { toast } from "sonner";
import { ChevronRight } from "lucide-react";

import { apiClient } from "@/services/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";

type TenantPlan = "free" | "starter" | "professional" | "enterprise";

interface Tenant {
  tenant_id: string;
  name: string;
  plan: string;
  max_users: number;
  is_active: boolean;
  created_at: string;
  settings: Record<string, unknown>;
}

interface TenantPromptResponse {
  tenant_id: string;
  prompts: Record<string, string>;
}

interface TenantCreatePayload {
  tenant_id: string;
  name: string;
  plan: TenantPlan;
  max_users: number;
  settings: Record<string, unknown>;
  bootstrap_admin?: {
    email: string;
    full_name: string;
    password: string;
  };
}

interface TenantUpdatePayload {
  name: string;
  plan: TenantPlan;
  max_users: number;
  is_active: boolean;
}

const PLAN_OPTIONS: TenantPlan[] = ["free", "starter", "professional", "enterprise"];
const TENANTS_PER_PAGE = 10;

function normalizePlan(plan: string): TenantPlan {
  if (plan === "free" || plan === "starter" || plan === "professional" || plan === "enterprise") {
    return plan;
  }
  // Backward compatibility for older values.
  if (plan === "growth") {
    return "professional";
  }
  return "free";
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

export default function TenantManagementPage() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [tenantsLoading, setTenantsLoading] = useState(false);
  const [includeInactive, setIncludeInactive] = useState(false);
  const [selectedTenantId, setSelectedTenantId] = useState<string>("");
  const [currentPage, setCurrentPage] = useState(1);
  const [createSheetOpen, setCreateSheetOpen] = useState(false);
  const [editSheetOpen, setEditSheetOpen] = useState(false);

  const [creating, setCreating] = useState(false);
  const [newTenantId, setNewTenantId] = useState("");
  const [newTenantName, setNewTenantName] = useState("");
  const [newTenantPlan, setNewTenantPlan] = useState<TenantPlan>("free");
  const [newTenantMaxUsers, setNewTenantMaxUsers] = useState("10");
  const [addBootstrapAdmin, setAddBootstrapAdmin] = useState(true);
  const [bootstrapEmail, setBootstrapEmail] = useState("");
  const [bootstrapName, setBootstrapName] = useState("");
  const [bootstrapPassword, setBootstrapPassword] = useState("");

  const [editing, setEditing] = useState(false);
  const [editTenantId, setEditTenantId] = useState("");
  const [editTenantName, setEditTenantName] = useState("");
  const [editTenantPlan, setEditTenantPlan] = useState<TenantPlan>("free");
  const [editTenantMaxUsers, setEditTenantMaxUsers] = useState("10");
  const [editTenantActive, setEditTenantActive] = useState(true);

  const [promptLoading, setPromptLoading] = useState(false);
  const [promptSaving, setPromptSaving] = useState(false);
  const [ragPrompt, setRagPrompt] = useState("");

  const loadTenants = useCallback(async () => {
    setTenantsLoading(true);
    try {
      const { data } = await apiClient.get<Tenant[]>("/api/v1/tenants", {
        params: {
          include_inactive: includeInactive,
          skip: 0,
          limit: 200,
        },
      });

      setTenants(data);
      if (!data.length) {
        setSelectedTenantId("");
        setRagPrompt("");
      } else {
        setSelectedTenantId((currentSelection) => {
          if (currentSelection && data.some((tenant) => tenant.tenant_id === currentSelection)) {
            return currentSelection;
          }
          return data[0]?.tenant_id ?? "";
        });
      }
    } catch (error) {
      toast.error(getErrorMessage(error, "Failed to load tenants"));
    } finally {
      setTenantsLoading(false);
    }
  }, [includeInactive]);

  const loadPrompts = useCallback(async (tenantId: string) => {
    if (!tenantId) {
      setRagPrompt("");
      return;
    }

    setPromptLoading(true);
    try {
      const { data } = await apiClient.get<TenantPromptResponse>(`/api/v1/tenants/${tenantId}/prompts`);
      setRagPrompt(data.prompts?.rag_system_v1 ?? "");
    } catch (error) {
      setRagPrompt("");
      toast.error(getErrorMessage(error, "Failed to load tenant prompt settings"));
    } finally {
      setPromptLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadTenants();
  }, [loadTenants]);

  useEffect(() => {
    if (selectedTenantId) {
      void loadPrompts(selectedTenantId);
    }
  }, [loadPrompts, selectedTenantId]);

  const totalPages = Math.max(1, Math.ceil(tenants.length / TENANTS_PER_PAGE));
  const startIndex = (currentPage - 1) * TENANTS_PER_PAGE;
  const endIndex = startIndex + TENANTS_PER_PAGE;
  const visibleTenants = tenants.slice(startIndex, endIndex);

  useEffect(() => {
    setCurrentPage((page) => Math.min(page, totalPages));
  }, [totalPages]);

  useEffect(() => {
    if (!selectedTenantId) {
      return;
    }

    const selectedIndex = tenants.findIndex((tenant) => tenant.tenant_id === selectedTenantId);
    if (selectedIndex < 0) {
      return;
    }

    const selectedPage = Math.floor(selectedIndex / TENANTS_PER_PAGE) + 1;
    setCurrentPage((page) => (page === selectedPage ? page : selectedPage));
  }, [selectedTenantId, tenants]);

  const resetCreateForm = () => {
    setNewTenantId("");
    setNewTenantName("");
    setNewTenantPlan("free");
    setNewTenantMaxUsers("10");
    setAddBootstrapAdmin(true);
    setBootstrapEmail("");
    setBootstrapName("");
    setBootstrapPassword("");
  };

  const handleCreateSheetChange = (open: boolean) => {
    setCreateSheetOpen(open);
    if (!open) {
      resetCreateForm();
    }
  };

  const openEditTenant = (tenant: Tenant) => {
    setEditTenantId(tenant.tenant_id);
    setEditTenantName(tenant.name);
    setEditTenantPlan(normalizePlan(tenant.plan));
    setEditTenantMaxUsers(String(tenant.max_users));
    setEditTenantActive(tenant.is_active);
    setEditSheetOpen(true);
  };

  const createTenant = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const normalizedTenantId = newTenantId.trim().toLowerCase();
    const normalizedTenantName = newTenantName.trim();
    const maxUsers = Number(newTenantMaxUsers);

    if (!normalizedTenantId || !normalizedTenantName || !Number.isFinite(maxUsers) || maxUsers < 1) {
      toast.error("Enter tenant ID, tenant name, and a valid max users value");
      return;
    }

    if (addBootstrapAdmin) {
      if (!bootstrapEmail.trim() || !bootstrapName.trim() || !bootstrapPassword.trim()) {
        toast.error("Bootstrap admin email, name, and password are required");
        return;
      }
    }

    const payload: TenantCreatePayload = {
      tenant_id: normalizedTenantId,
      name: normalizedTenantName,
      plan: newTenantPlan,
      max_users: Math.floor(maxUsers),
      settings: {},
    };

    if (addBootstrapAdmin) {
      payload.bootstrap_admin = {
        email: bootstrapEmail.trim(),
        full_name: bootstrapName.trim(),
        password: bootstrapPassword,
      };
    }

    setCreating(true);
    try {
      await apiClient.post("/api/v1/tenants", payload);
      toast.success("Tenant created");
      resetCreateForm();
      setCreateSheetOpen(false);

      await loadTenants();
      setSelectedTenantId(normalizedTenantId);
    } catch (error) {
      toast.error(getErrorMessage(error, "Failed to create tenant"));
    } finally {
      setCreating(false);
    }
  };

  const updateTenant = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const tenantId = editTenantId.trim();
    const normalizedName = editTenantName.trim();
    const maxUsers = Number(editTenantMaxUsers);

    if (!tenantId) {
      toast.error("Select a tenant first");
      return;
    }

    if (!normalizedName || !Number.isFinite(maxUsers) || maxUsers < 1) {
      toast.error("Enter tenant name and a valid max users value");
      return;
    }

    const payload: TenantUpdatePayload = {
      name: normalizedName,
      plan: editTenantPlan,
      max_users: Math.floor(maxUsers),
      is_active: editTenantActive,
    };

    setEditing(true);
    try {
      await apiClient.patch(`/api/v1/tenants/${tenantId}`, payload);
      toast.success("Tenant updated");
      setEditSheetOpen(false);
      await loadTenants();
      setSelectedTenantId(tenantId);
    } catch (error) {
      toast.error(getErrorMessage(error, "Failed to update tenant"));
    } finally {
      setEditing(false);
    }
  };

  const savePrompt = async () => {
    const tenantId = selectedTenantId;
    if (!tenantId) {
      toast.error("Select a tenant first");
      return;
    }

    if (ragPrompt.trim().length < 20) {
      toast.error("Prompt must be at least 20 characters");
      return;
    }

    setPromptSaving(true);
    try {
      await apiClient.patch(`/api/v1/tenants/${tenantId}/prompts`, {
        rag_system_v1: ragPrompt,
      });
      toast.success("Tenant prompt updated");
      await loadPrompts(tenantId);
    } catch (error) {
      toast.error(getErrorMessage(error, "Failed to update tenant prompt"));
    } finally {
      setPromptSaving(false);
    }
  };

  const toggleTenantAccordion = (tenantId: string) => {
    if (selectedTenantId === tenantId) {
      setSelectedTenantId("");
      setRagPrompt("");
      return;
    }

    setSelectedTenantId(tenantId);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Tenant Management</h1>
          <p className="text-sm text-muted-foreground">
            Tenant list, create/edit tenant controls, and tenant-specific RAG prompt configuration in one place.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Checkbox
            checked={includeInactive}
            onChange={(event) => setIncludeInactive(event.currentTarget.checked)}
            label="Include inactive"
          />
          <Button type="button" variant="outline" onClick={() => void loadTenants()} disabled={tenantsLoading}>
            {tenantsLoading ? "Refreshing..." : "Refresh"}
          </Button>
          <Button type="button" onClick={() => setCreateSheetOpen(true)}>
            Create Tenant
          </Button>
        </div>
      </div>

      <section className="rounded-lg border bg-white p-5 shadow-sm">
        <h2 className="text-lg font-semibold">Tenant Registry</h2>
        <p className="mt-1 text-xs text-muted-foreground">
          Accordion view: expand a tenant to manage details and prompt settings inline.
        </p>

        {!tenantsLoading && tenants.length === 0 && (
          <div className="mt-6 text-center text-sm text-muted-foreground">No tenants found.</div>
        )}

        <div className="mt-4 space-y-3">
          {visibleTenants.map((tenant) => {
            const expanded = tenant.tenant_id === selectedTenantId;

            return (
              <div key={tenant.tenant_id} className="rounded-lg border border-gray-200">
                <button
                  type="button"
                  className={`w-full px-4 py-3 text-left transition-colors hover:bg-gray-50 ${expanded ? "bg-blue-50" : ""}`}
                  onClick={() => toggleTenantAccordion(tenant.tenant_id)}
                  aria-expanded={expanded}
                  aria-controls={`tenant-panel-${tenant.tenant_id}`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex min-w-0 items-center gap-3">
                      <ChevronRight
                        className={`h-4 w-4 shrink-0 text-muted-foreground transition-transform ${expanded ? "rotate-90" : ""}`}
                        aria-hidden="true"
                      />
                      <div className="min-w-0">
                        <div className="font-medium">{tenant.tenant_id}</div>
                        <div className="text-xs text-muted-foreground">{tenant.name}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <span className="rounded-full bg-gray-100 px-2 py-0.5">plan: {tenant.plan}</span>
                      <span className="rounded-full bg-gray-100 px-2 py-0.5">users: {tenant.max_users}</span>
                      <span
                        className={`rounded-full px-2 py-0.5 ${
                          tenant.is_active ? "bg-emerald-100 text-emerald-700" : "bg-gray-200 text-gray-700"
                        }`}
                      >
                        {tenant.is_active ? "active" : "inactive"}
                      </span>
                    </div>
                  </div>
                </button>

                <div
                  id={`tenant-panel-${tenant.tenant_id}`}
                  aria-hidden={!expanded}
                  className={`overflow-hidden transition-[max-height,opacity] duration-300 ease-out ${
                    expanded ? "max-h-[900px] opacity-100" : "max-h-0 opacity-0"
                  }`}
                >
                  <div className="space-y-4 border-t px-4 py-4">
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm">
                        <span className="font-medium">Tenant ID:</span> {tenant.tenant_id}
                      </div>
                      <Button type="button" size="sm" variant="outline" onClick={() => openEditTenant(tenant)}>
                        Edit Tenant
                      </Button>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor={`rag-prompt-${tenant.tenant_id}`}>rag_system_v1</Label>
                      <Textarea
                        id={`rag-prompt-${tenant.tenant_id}`}
                        rows={6}
                        value={ragPrompt}
                        onChange={(event) => setRagPrompt(event.target.value)}
                        placeholder="Enter tenant-specific RAG system prompt..."
                        disabled={promptLoading || !expanded}
                      />
                      <div className="text-xs text-muted-foreground">
                        {promptLoading ? "Loading prompt..." : `Editing prompt for ${tenant.tenant_id}`}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      <Button type="button" onClick={savePrompt} disabled={promptLoading || promptSaving || !expanded}>
                        {promptSaving ? "Saving..." : "Save Prompt"}
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => void loadPrompts(tenant.tenant_id)}
                        disabled={promptLoading || promptSaving || !expanded}
                      >
                        Reload
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {tenants.length > TENANTS_PER_PAGE && (
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t pt-4">
            <div className="text-xs text-muted-foreground">
              Showing {startIndex + 1}-{Math.min(endIndex, tenants.length)} of {tenants.length} tenants
            </div>
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage((page) => Math.max(1, page - 1))}
                disabled={currentPage === 1}
              >
                Previous
              </Button>
              <span className="text-xs text-muted-foreground">
                Page {currentPage} of {totalPages}
              </span>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage((page) => Math.min(totalPages, page + 1))}
                disabled={currentPage === totalPages}
              >
                Next
              </Button>
            </div>
          </div>
        )}
      </section>

      <Sheet open={createSheetOpen} onOpenChange={handleCreateSheetChange}>
        <SheetContent side="right" className="w-full sm:w-1/2 sm:max-w-[50vw] overflow-y-auto">
          <SheetHeader>
            <SheetTitle>Create Tenant</SheetTitle>
            <SheetDescription>
              Create tenant from side panel. Tenant ID must use lowercase letters, numbers, and hyphens.
            </SheetDescription>
          </SheetHeader>

          <form onSubmit={createTenant} className="mt-6 space-y-4">
            <div className="space-y-4">
              <div className="space-y-1">
                <Label htmlFor="create-tenant-id">Tenant ID</Label>
                <Input
                  id="create-tenant-id"
                  value={newTenantId}
                  onChange={(event) => setNewTenantId(event.target.value)}
                  placeholder="moh"
                  required
                />
              </div>

              <div className="space-y-1">
                <Label htmlFor="create-tenant-name">Tenant Name</Label>
                <Input
                  id="create-tenant-name"
                  value={newTenantName}
                  onChange={(event) => setNewTenantName(event.target.value)}
                  placeholder="Ministry of Health"
                  required
                />
              </div>

              <div className="space-y-1">
                <Label htmlFor="create-tenant-plan">Plan</Label>
                <select
                  id="create-tenant-plan"
                  className="flex h-9 w-full rounded-md border border-gray-300 bg-white px-3 py-1 text-sm"
                  value={newTenantPlan}
                  onChange={(event) => setNewTenantPlan(event.target.value as TenantPlan)}
                >
                  {PLAN_OPTIONS.map((planOption) => (
                    <option key={planOption} value={planOption}>
                      {planOption}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-1">
                <Label htmlFor="create-tenant-max-users">Max Users</Label>
                <Input
                  id="create-tenant-max-users"
                  type="number"
                  min={1}
                  value={newTenantMaxUsers}
                  onChange={(event) => setNewTenantMaxUsers(event.target.value)}
                  required
                />
              </div>
            </div>

            <div>
              <Checkbox
                checked={addBootstrapAdmin}
                onChange={(event) => setAddBootstrapAdmin(event.currentTarget.checked)}
                label="Create bootstrap tenant admin"
              />
            </div>

            {addBootstrapAdmin && (
              <div className="space-y-4">
                <div className="space-y-1">
                  <Label htmlFor="create-bootstrap-email">Admin Email</Label>
                  <Input
                    id="create-bootstrap-email"
                    type="email"
                    value={bootstrapEmail}
                    onChange={(event) => setBootstrapEmail(event.target.value)}
                    placeholder="admin@moh.com"
                    required
                  />
                </div>

                <div className="space-y-1">
                  <Label htmlFor="create-bootstrap-name">Admin Name</Label>
                  <Input
                    id="create-bootstrap-name"
                    value={bootstrapName}
                    onChange={(event) => setBootstrapName(event.target.value)}
                    placeholder="MOH Admin"
                    required
                  />
                </div>

                <div className="space-y-1">
                  <Label htmlFor="create-bootstrap-password">Admin Password</Label>
                  <Input
                    id="create-bootstrap-password"
                    type="password"
                    minLength={8}
                    value={bootstrapPassword}
                    onChange={(event) => setBootstrapPassword(event.target.value)}
                    placeholder="Minimum 8 characters"
                    required
                  />
                </div>
              </div>
            )}

            <SheetFooter className="pt-2">
              <SheetClose asChild>
                <Button type="button" variant="outline">Cancel</Button>
              </SheetClose>
              <Button type="submit" disabled={creating}>
                {creating ? "Creating..." : "Create Tenant"}
              </Button>
            </SheetFooter>
          </form>
        </SheetContent>
      </Sheet>

      <Sheet open={editSheetOpen} onOpenChange={setEditSheetOpen}>
        <SheetContent side="right" className="w-full sm:w-1/2 sm:max-w-[50vw] overflow-y-auto">
          <SheetHeader>
            <SheetTitle>Edit Tenant</SheetTitle>
            <SheetDescription>Update tenant details from side panel.</SheetDescription>
          </SheetHeader>

          <form onSubmit={updateTenant} className="mt-6 space-y-4">
            <div className="space-y-1">
              <Label htmlFor="edit-tenant-id">Tenant ID</Label>
              <Input id="edit-tenant-id" value={editTenantId} disabled />
            </div>

            <div className="space-y-1">
              <Label htmlFor="edit-tenant-name">Tenant Name</Label>
              <Input
                id="edit-tenant-name"
                value={editTenantName}
                onChange={(event) => setEditTenantName(event.target.value)}
                required
              />
            </div>

            <div className="space-y-1">
              <Label htmlFor="edit-tenant-plan">Plan</Label>
              <select
                id="edit-tenant-plan"
                className="flex h-9 w-full rounded-md border border-gray-300 bg-white px-3 py-1 text-sm"
                value={editTenantPlan}
                onChange={(event) => setEditTenantPlan(event.target.value as TenantPlan)}
              >
                {PLAN_OPTIONS.map((planOption) => (
                  <option key={planOption} value={planOption}>
                    {planOption}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1">
              <Label htmlFor="edit-tenant-max-users">Max Users</Label>
              <Input
                id="edit-tenant-max-users"
                type="number"
                min={1}
                value={editTenantMaxUsers}
                onChange={(event) => setEditTenantMaxUsers(event.target.value)}
                required
              />
            </div>

            <div>
              <Checkbox
                checked={editTenantActive}
                onChange={(event) => setEditTenantActive(event.currentTarget.checked)}
                label="Tenant is active"
              />
            </div>

            <SheetFooter className="pt-2">
              <SheetClose asChild>
                <Button type="button" variant="outline">Cancel</Button>
              </SheetClose>
              <Button type="submit" disabled={editing}>
                {editing ? "Saving..." : "Save Changes"}
              </Button>
            </SheetFooter>
          </form>
        </SheetContent>
      </Sheet>
    </div>
  );
}
