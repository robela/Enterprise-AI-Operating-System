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

  // Show a simple loading/redirect indicator
  return (
    <div className="flex items-center justify-center min-h-screen bg-white">
      <div className="text-center">
        <h1 className="text-2xl font-semibold mb-2">Loading...</h1>
        <p className="text-gray-600">Redirecting you to the appropriate page</p>
      </div>
    </div>
  );
}
