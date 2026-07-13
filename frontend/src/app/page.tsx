"use client";

import { useAuth } from "@/utils/auth";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function HomePage() {
  const router = useRouter();
  const { token, isLoading } = useAuth();

  useEffect(() => {
    console.log('[HomePage] Auth state:', { token: !!token, isLoading });
    
    if (isLoading) return;
    
    // Redirect authenticated users to dashboard, unauthenticated to login
    if (token) {
      console.log('[HomePage] User authenticated, redirecting to /dashboard');
      router.push("/dashboard");
    } else {
      console.log('[HomePage] User not authenticated, redirecting to /login');
      router.push("/login");
    }
  }, [token, isLoading, router]);

  // Show a simple loading indicator while checking authentication
  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="text-center space-y-4">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-indigo-200 animate-pulse">
          <div className="w-8 h-8 rounded-full border-4 border-indigo-300 border-t-indigo-600 animate-spin"></div>
        </div>
        <h1 className="text-2xl font-semibold text-gray-800">Loading...</h1>
        <p className="text-gray-600">Redirecting you to the appropriate page</p>
      </div>
    </div>
  );
}
