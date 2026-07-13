import { useState, useCallback } from "react";
import { userService } from "@/services/api/users";
import type { User } from "@/types/user";

export function useUserManagement() {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchUsers = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await userService.getList();
      setUsers(data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)));
    } finally {
      setIsLoading(false);
    }
  }, []);

  const deleteUser = useCallback(async (userId: number) => {
    await userService.delete(userId);
    setUsers((prev) => prev.filter((u) => u.id !== userId));
  }, []);

  return { users, isLoading, error, fetchUsers, deleteUser };
}
