"use client";

import { useRouter } from "next/navigation";
import { useAuth } from "@/utils/auth";
import type { UserRole } from "@/utils/types";
import { ReactNode, useEffect } from "react";

interface ProtectedComponentProps {
  children: ReactNode;
  authorizedRoles: UserRole[];
}

export function ProtectedComponent({
  children,
  authorizedRoles,
}: ProtectedComponentProps) {
  const { token, role, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;

    if (!token) {
      router.replace("/login");
      return;
    }

    if (role && !authorizedRoles.includes(role)) {
      router.replace("/chat");
    }
  }, [authorizedRoles, isLoading, role, router, token]);

  if (isLoading) return null;

  if (!token) {
    return null;
  }

  if (role && !authorizedRoles.includes(role)) {
    return null;
  }

  return <>{children}</>;
}
