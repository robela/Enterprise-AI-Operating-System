import { z } from "zod";

export const documentSchema = z.object({
  document_id: z.string(),
  filename: z.string(),
  status: z.enum(["pending", "processing", "indexed", "failed"]),
});

export const documentUploadSchema = z.object({
  document_id: z.string(),
  status: z.enum(["pending", "processing", "indexed", "failed"]),
  chunk_count: z.number(),
});

export type Document = z.infer<typeof documentSchema>;
export type DocumentUploadResult = z.infer<typeof documentUploadSchema>;
