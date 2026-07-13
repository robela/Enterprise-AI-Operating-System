import { z } from "zod";

export const documentSchema = z.object({
  id: z.number(),
  name: z.string(),
  content_type: z.string(),
  size_bytes: z.number(),
  created_at: z.string(),
  tenant_id: z.string().optional(),
});

export type Document = z.infer<typeof documentSchema>;
