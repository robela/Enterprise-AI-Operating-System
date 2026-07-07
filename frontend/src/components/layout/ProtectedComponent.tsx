"use client";

import { useRouter } from "next/navigation";
import { useAuth } from "@/utils/auth";
import type { UserRole } from "@/utils/types";
import { ReactNode } from "react";

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

  if (isLoading) return null;

  if (!token) {
    router.replace("/login");
    return null;
  }

  if (role && !authorizedRoles.includes(role)) {
    router.replace("/chat");
    return null;
  }

  return <>{children}</>;
}
