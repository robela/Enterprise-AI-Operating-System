import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/utils/auth";
import { Toaster } from "sonner";

export const metadata: Metadata = {
  title: "Enterprise AI OS",
  description: "Enterprise AI Operating System — multi-tenant AI platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <AuthProvider>
          {children}
          <Toaster position="top-right" richColors />
        </AuthProvider>
      </body>
    </html>
  );
}
