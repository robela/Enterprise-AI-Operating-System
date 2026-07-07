"use client";

import { useEffect } from "react";
import { useDashboardMetrics } from "@/hooks/useDashboardMetrics";

export function DashboardClient() {
  const { metrics, isLoading, error, fetchMetrics } = useDashboardMetrics();

  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  if (error) {
    return (
      <div className="text-destructive text-sm">
        Failed to load dashboard: {error.message}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {isLoading
          ? Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className="bg-card border rounded-lg p-5 animate-pulse h-24"
              />
            ))
          : metrics.map((m) => (
              <div key={m.label} className="bg-card border rounded-lg p-5">
                <p className="text-muted-foreground text-sm">{m.label}</p>
                <p className="text-3xl font-bold mt-1">{m.value}</p>
                {m.change !== undefined && (
                  <p
                    className={`text-xs mt-1 ${
                      m.change >= 0 ? "text-green-600" : "text-destructive"
                    }`}
                  >
                    {m.change >= 0 ? "+" : ""}
                    {m.change}% this month
                  </p>
                )}
              </div>
            ))}
      </div>
    </div>
  );
}
