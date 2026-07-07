import { z } from "zod";

export const userSchema = z.object({
  id: z.number(),
  email: z.string().email(),
  role: z.enum(["admin", "user", "callAgent"]),
  created_at: z.string(),
  is_active: z.boolean().default(true),
});

export const createUserSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  role: z.enum(["admin", "user", "callAgent"]),
});

export const updateUserSchema = createUserSchema.partial();

export type User = z.infer<typeof userSchema>;
export type UserCreate = z.infer<typeof createUserSchema>;
export type UserUpdate = z.infer<typeof updateUserSchema>;
