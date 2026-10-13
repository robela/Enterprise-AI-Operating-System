"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";

import type { User } from "@/types/user";

import { AddUserForm } from "./components/AddUserForm";
import { UserTable } from "./components/UserTable";
import { useUserManagement } from "./hooks/useUserManagement";

export function UsersClient() {
  const { users, isLoading, error, fetchUsers, deleteUser, activateUser, resetUserPassword } = useUserManagement();
  const [editingUser, setEditingUser] = useState<User | null>(null);

  useEffect(() => {
    void fetchUsers();
  }, [fetchUsers]);

  const handleDelete = async (userId: string) => {
    try {
      await deleteUser(userId);
      toast.success("User deleted");
    } catch {
      toast.error("Failed to delete user");
    }
  };

  const handleActivate = async (userId: string) => {
    try {
      await activateUser(userId);
      toast.success("User activated");
    } catch {
      toast.error("Failed to activate user");
    }
  };

  const handleResetPassword = async (user: User) => {
    const password = window.prompt(`Set a new password for ${user.email}`);
    if (password === null) return;
    if (password.length < 8) {
      toast.error("Password must be at least 8 characters");
      return;
    }

    try {
      await resetUserPassword(user.id, password);
      toast.success("Password reset successfully");
    } catch {
      toast.error("Failed to reset password");
    }
  };

  if (error) {
    return <div className="text-destructive text-sm">Failed to load users: {error.message}</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Users</h1>
        <AddUserForm onSuccess={fetchUsers} />
      </div>

      <UserTable
        users={users}
        isLoading={isLoading}
        onEdit={setEditingUser}
        onActivate={handleActivate}
        onResetPassword={handleResetPassword}
        onDelete={handleDelete}
      />

      {editingUser && <p className="text-sm text-muted-foreground">Editing: {editingUser.email}</p>}
    </div>
  );
}
