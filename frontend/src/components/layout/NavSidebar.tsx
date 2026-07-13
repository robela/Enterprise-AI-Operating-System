"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/utils/auth";
import {
  LayoutDashboard,
  Users,
  FileText,
  MessageSquare,
  ClipboardList,
  LogOut,
} from "lucide-react";

const navItems = [
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
    roles: ["admin"],
  },
  { label: "Users", href: "/users", icon: Users, roles: ["admin"] },
  {
    label: "Documents",
    href: "/documents",
    icon: FileText,
    roles: ["admin"],
  },
  {
    label: "Audit",
    href: "/audit",
    icon: ClipboardList,
    roles: ["admin"],
  },
  {
    label: "Chat",
    href: "/chat",
    icon: MessageSquare,
    roles: ["admin", "user", "callAgent"],
  },
];

export function NavSidebar() {
  const pathname = usePathname();
  const { role, username, logout } = useAuth();

  const visible = navItems.filter(
    (item) => role && item.roles.includes(role)
  );

  return (
    <aside className="w-60 flex flex-col bg-sidebar text-sidebar-foreground border-r border-sidebar-border h-full">
      <div className="px-6 py-5 border-b border-sidebar-border">
        <span className="font-bold text-sm tracking-wide uppercase">
          Enterprise AI OS
        </span>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {visible.map(({ label, href, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                active
                  ? "bg-white/10 font-medium"
                  : "hover:bg-white/5 text-sidebar-foreground/70 hover:text-sidebar-foreground"
              }`}
            >
              <Icon size={16} />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="px-4 py-4 border-t border-sidebar-border">
        <div className="text-xs text-sidebar-foreground/60 mb-2 truncate">
          {username}
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-2 text-sm text-sidebar-foreground/70 hover:text-sidebar-foreground transition-colors w-full"
        >
          <LogOut size={14} />
          Sign out
        </button>
      </div>
    </aside>
  );
}
