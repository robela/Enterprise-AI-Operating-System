"use client";

import { useAuth } from "@/utils/auth";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function HomePage() {
  const router = useRouter();
  const { token, isLoading } = useAuth();

  useEffect(() => {
    if (isLoading) return;
    
    // Redirect authenticated users to dashboard, unauthenticated to login
    if (token) {
      router.push("/dashboard");
    } else {
      router.push("/login");
    }
  }, [token, isLoading, router]);

  // Show nothing while checking authentication
  return null;
}
