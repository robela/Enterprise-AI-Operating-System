import { z } from "zod";

export const documentTypeSchema = z.enum([
  "primary",
  "secondary",
  "pdf",
  "word",
  "excel",
  "text",
  "markdown",
  "html",
  "other",
]);

export const lifecycleStatusSchema = z.enum(["active", "inactive"]);

export const documentSchema = z.object({
  document_id: z.string(),
  filename: z.string(),
  status: z.enum(["pending", "processing", "indexed", "failed"]),
  doc_type: documentTypeSchema.optional(),
  lifecycle_status: lifecycleStatusSchema.optional(),
});

export const documentUploadSchema = z.object({
  document_id: z.string(),
  status: z.enum(["pending", "processing", "indexed", "failed"]),
  chunk_count: z.number(),
  doc_type: documentTypeSchema.optional(),
  lifecycle_status: lifecycleStatusSchema.optional(),
});

export const documentUploadOptionsSchema = z.object({
  document_type: documentTypeSchema.optional(),
  lifecycle_status: lifecycleStatusSchema.optional(),
});

export type Document = z.infer<typeof documentSchema>;
export type DocumentUploadResult = z.infer<typeof documentUploadSchema>;
export type DocumentTypeValue = z.infer<typeof documentTypeSchema>;
export type LifecycleStatus = z.infer<typeof lifecycleStatusSchema>;
export type DocumentUploadOptions = z.infer<typeof documentUploadOptionsSchema>;
