import { ProtectedComponent } from "@/components/layout/ProtectedComponent";

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedComponent authorizedRoles={["admin"]}>
      {children}
    </ProtectedComponent>
  );
}
