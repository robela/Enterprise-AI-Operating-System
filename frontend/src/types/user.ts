import { z } from "zod";

const userRoleSchema = z.enum(["admin", "tenant_admin", "tenant_user"]);

export const userSchema = z.object({
  id: z.string(),
  email: z.string().email(),
  full_name: z.string(),
  role: userRoleSchema,
  created_at: z.string(),
  is_active: z.boolean().default(true),
  tenant_id: z.string().optional(),
});

const createUserBaseSchema = z.object({
  email: z.string().email("Invalid email address"),
  full_name: z.string().min(1, "Full name is required"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  role: userRoleSchema,
  tenant_id: z.string().trim().optional(),
});

export const createUserSchema = createUserBaseSchema
  .superRefine((data, ctx) => {
    if (data.role !== "admin" && !data.tenant_id) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["tenant_id"],
        message: "Tenant is required for tenant roles",
      });
    }
  });

export const updateUserSchema = createUserBaseSchema.partial();

export type User = z.infer<typeof userSchema>;
export type UserCreate = z.infer<typeof createUserSchema>;
export type UserUpdate = z.infer<typeof updateUserSchema>;
