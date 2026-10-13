import { useCallback, useState } from "react";

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

  const deleteUser = useCallback(async (userId: string) => {
    await userService.delete(userId);
    setUsers((prev) => prev.filter((user) => user.id !== userId));
  }, []);

  const activateUser = useCallback(async (userId: string) => {
    const activatedUser = await userService.activate(userId);
    setUsers((prev) => prev.map((user) => (user.id === userId ? activatedUser : user)));
  }, []);

  return { users, isLoading, error, fetchUsers, deleteUser, activateUser };
}
