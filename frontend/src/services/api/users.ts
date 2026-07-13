import { apiClient } from "./client";
import { userSchema, createUserSchema, type User, type UserCreate } from "@/types/user";

export const userService = {
  async getList(): Promise<User[]> {
    const { data } = await apiClient.get("/api/v1/users");
    return (data as unknown[]).map((u) => userSchema.parse(u));
  },

  async getById(id: number): Promise<User> {
    const { data } = await apiClient.get(`/api/v1/users/${id}`);
    return userSchema.parse(data);
  },

  async create(user: UserCreate): Promise<User> {
    const validated = createUserSchema.parse(user);
    const { data } = await apiClient.post("/api/v1/users", validated);
    return userSchema.parse(data);
  },

  async update(id: number, user: Partial<UserCreate>): Promise<User> {
    const { data } = await apiClient.patch(`/api/v1/users/${id}`, user);
    return userSchema.parse(data);
  },

  async delete(id: number): Promise<void> {
    await apiClient.delete(`/api/v1/users/${id}`);
  },
};
