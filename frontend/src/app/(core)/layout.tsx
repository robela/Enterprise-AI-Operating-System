import { NavSidebar } from "@/components/layout/NavSidebar";
import { ProtectedComponent } from "@/components/layout/ProtectedComponent";

export default function CoreLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedComponent authorizedRoles={["admin", "user", "callAgent"]}>
      <div className="flex h-screen overflow-hidden">
        <NavSidebar />
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </ProtectedComponent>
  );
}
