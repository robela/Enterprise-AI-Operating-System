import { apiClient } from "./client";
import { userSchema, createUserSchema, type User, type UserCreate } from "@/types/user";

const backendUserSchema = userSchema.extend({
  id: userSchema.shape.id.optional(),
}).passthrough();

type BackendUser = {
  user_id: string;
  email: string;
  full_name: string;
  roles: string[];
  status: string;
  created_at: string;
};

function normalizeUser(user: BackendUser): User {
  const primaryRole = user.roles.find(
    (role): role is User["role"] => role === "admin" || role === "user" || role === "callAgent"
  ) ?? "user";

  return userSchema.parse({
    id: user.user_id,
    email: user.email,
    full_name: user.full_name,
    role: primaryRole,
    created_at: user.created_at,
    is_active: user.status === "active",
  });
}

export const userService = {
  async getList(): Promise<User[]> {
    const { data } = await apiClient.get("/api/v1/users");
    const items = Array.isArray(data) ? data : (data as { items?: unknown[] }).items ?? [];
    return items.map((user) => normalizeUser(user as BackendUser));
  },

  async getById(id: string): Promise<User> {
    const { data } = await apiClient.get(`/api/v1/users/${id}`);
    return normalizeUser(data as BackendUser);
  },

  async create(user: UserCreate): Promise<User> {
    const validated = createUserSchema.parse(user);
    const payload = {
      email: validated.email,
      full_name: validated.full_name,
      password: validated.password,
      roles: [validated.role],
    };
    const { data } = await apiClient.post("/api/v1/users", payload);
    return normalizeUser(data as BackendUser);
  },

  async update(id: string, user: Partial<UserCreate>): Promise<User> {
    const payload = {
      full_name: user.full_name,
      roles: user.role ? [user.role] : undefined,
    };
    const { data } = await apiClient.patch(`/api/v1/users/${id}`, payload);
    return normalizeUser(data as BackendUser);
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/api/v1/users/${id}`);
  },
};
