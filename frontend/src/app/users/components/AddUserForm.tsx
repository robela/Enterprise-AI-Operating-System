"use client";

import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";

import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { apiClient } from "@/services/api/client";
import { userService } from "@/services/api/users";
import { createUserSchema, type UserCreate } from "@/types/user";
import { useAuth } from "@/utils/auth";

interface TenantOption {
  tenant_id: string;
  name?: string;
}

interface AddUserFormProps {
  onSuccess: () => void;
}

export function AddUserForm({ onSuccess }: AddUserFormProps) {
  const [open, setOpen] = useState(false);
  const [tenantOptions, setTenantOptions] = useState<TenantOption[]>([]);
  const [loadingTenants, setLoadingTenants] = useState(false);
  const { tenant_id: currentTenantId, role: currentRole } = useAuth();

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<UserCreate>({
    resolver: zodResolver(createUserSchema),
    defaultValues: {
      role: "tenant_user",
      tenant_id: currentTenantId ?? "",
    },
  });

  const selectedRole = watch("role");
  const needsTenant = selectedRole !== "admin";

  useEffect(() => {
    setValue("tenant_id", currentTenantId ?? "");
  }, [currentTenantId, setValue]);

  useEffect(() => {
    const loadTenants = async () => {
      if (!open) return;

      setLoadingTenants(true);
      try {
        // Admin can pick from all tenants; tenant admins are constrained to their own tenant.
        if (currentRole === "admin") {
          const { data } = await apiClient.get<TenantOption[]>("/api/v1/tenants", {
            params: { include_inactive: false, skip: 0, limit: 200 },
          });
          const options = Array.isArray(data) ? data : [];
          setTenantOptions(options);
          const firstOption = options[0];
          if (!watch("tenant_id") && firstOption) {
            setValue("tenant_id", firstOption.tenant_id);
          }
        } else if (currentTenantId) {
          setTenantOptions([{ tenant_id: currentTenantId, name: currentTenantId }]);
          setValue("tenant_id", currentTenantId);
        }
      } catch {
        if (currentTenantId) {
          setTenantOptions([{ tenant_id: currentTenantId, name: currentTenantId }]);
          setValue("tenant_id", currentTenantId);
        } else {
          setTenantOptions([]);
        }
      } finally {
        setLoadingTenants(false);
      }
    };

    void loadTenants();
  }, [open, currentRole, currentTenantId, setValue, watch]);

  const onSubmit = async (data: UserCreate) => {
    if (data.role !== "admin" && !data.tenant_id) {
      toast.error("Please choose a tenant for tenant roles");
      return;
    }

    try {
      await userService.create(data);
      toast.success("User created successfully");
      reset();
      setOpen(false);
      onSuccess();
    } catch {
      toast.error("Failed to create user");
    }
  };

  const handleOpenChange = (nextOpen: boolean) => {
    setOpen(nextOpen);
    if (!nextOpen) {
      reset({ role: "tenant_user", tenant_id: currentTenantId ?? "" });
    }
  };

  return (
    <Sheet open={open} onOpenChange={handleOpenChange}>
      <SheetTrigger asChild>
        <button
          type="button"
          className="bg-primary text-primary-foreground px-4 py-2 rounded-md text-sm font-medium hover:opacity-90 transition-opacity"
        >
          Add User
        </button>
      </SheetTrigger>

      <SheetContent side="right" className="w-full sm:max-w-xl overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Add New User</SheetTitle>
          <SheetDescription>
            Create a new tenant user from this side panel.
          </SheetDescription>
        </SheetHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="mt-6 space-y-4">
          <div className="space-y-1">
            <label className="text-sm font-medium">Full Name</label>
            <input
              type="text"
              className="w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              {...register("full_name")}
            />
            {errors.full_name && <p className="text-destructive text-xs">{errors.full_name.message}</p>}
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium">Email</label>
            <input
              type="email"
              className="w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              {...register("email")}
            />
            {errors.email && <p className="text-destructive text-xs">{errors.email.message}</p>}
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium">Password</label>
            <input
              type="password"
              className="w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              {...register("password")}
            />
            {errors.password && <p className="text-destructive text-xs">{errors.password.message}</p>}
          </div>

          <div className="space-y-1">
            <label className="text-sm font-medium">Role</label>
            <select
              className="w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              {...register("role")}
            >
              <option value="admin">Admin</option>
              <option value="tenant_admin">Tenant Admin</option>
              <option value="tenant_user">Tenant User</option>
            </select>
            {errors.role && <p className="text-destructive text-xs">{errors.role.message}</p>}
          </div>

          {needsTenant && (
            <div className="space-y-1">
              <label className="text-sm font-medium">Tenant</label>
              <select
                className="w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                {...register("tenant_id")}
              >
                <option value="">Select tenant</option>
                {tenantOptions.map((tenant) => (
                  <option key={tenant.tenant_id} value={tenant.tenant_id}>
                    {tenant.tenant_id}{tenant.name ? ` (${tenant.name})` : ""}
                  </option>
                ))}
              </select>
              {loadingTenants && <p className="text-xs text-muted-foreground">Loading tenants...</p>}
              {errors.tenant_id && <p className="text-destructive text-xs">{errors.tenant_id.message}</p>}
            </div>
          )}

          <SheetFooter className="pt-2">
            <SheetClose asChild>
              <button
                type="button"
                className="border rounded-md py-2 px-4 text-sm hover:bg-accent transition-colors"
              >
                Cancel
              </button>
            </SheetClose>
            <button
              type="submit"
              disabled={isSubmitting}
              className="bg-primary text-primary-foreground rounded-md py-2 px-4 text-sm font-medium hover:opacity-90 disabled:opacity-60 transition-opacity"
            >
              {isSubmitting ? "Creating..." : "Create"}
            </button>
          </SheetFooter>
        </form>
      </SheetContent>
    </Sheet>
  );
}
