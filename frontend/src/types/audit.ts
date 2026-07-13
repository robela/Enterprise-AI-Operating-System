import { z } from "zod";

export const auditLogSchema = z.object({
  id: z.number(),
  action: z.string(),
  user_id: z.number().nullable().optional(),
  ip_address: z.string().nullable().optional(),
  result: z.string(),
  created_at: z.string(),
  resource_type: z.string().optional(),
  resource_id: z.string().nullable().optional(),
});

export type AuditLog = z.infer<typeof auditLogSchema>;
