"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("token") || localStorage.getItem("access_token");
    if (token) {
      router.replace("/chat");
    } else {
      router.replace("/login");
    }
  }, [router]);

  return (
    <div style={{ padding: "20px", textAlign: "center" }}>
      <p>Redirecting...</p>
    </div>
  );
}
