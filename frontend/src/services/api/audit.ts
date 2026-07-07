import { apiClient } from "./client";
import { auditLogSchema, type AuditLog } from "@/types/audit";

export const auditService = {
  async getLogs(): Promise<AuditLog[]> {
    const { data } = await apiClient.get("/api/v1/audit");
    return (data as unknown[]).map((l) => auditLogSchema.parse(l));
  },
};
