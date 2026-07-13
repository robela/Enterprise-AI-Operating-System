import { apiClient } from "./client";
import type { DashboardMetric } from "@/hooks/useDashboardMetrics";

export const dashboardService = {
  async getMetrics(): Promise<DashboardMetric[]> {
    const { data } = await apiClient.get("/api/v1/analytics/metrics");
    return data as DashboardMetric[];
  },
};
