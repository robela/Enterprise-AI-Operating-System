"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/utils/auth";
import { useConversations } from "@/app/chat/hooks/useConversations";
import {
  Building2,
  ChevronRight,
  LayoutDashboard,
  Users,
  FileText,
  MessageSquare,
  Plus,
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
  { label: "Users", href: "/users", icon: Users, roles: ["admin", "tenant_admin"] },
  {
    label: "Documents",
    href: "/documents",
    icon: FileText,
    roles: ["admin", "tenant_admin"],
  },
  {
    label: "Audit",
    href: "/audit",
    icon: ClipboardList,
    roles: ["admin"],
  },
  {
    label: "Tenants",
    href: "/tenants",
    icon: Building2,
    roles: ["admin"],
  },
  {
    label: "Chat",
    href: "/chat",
    icon: MessageSquare,
    roles: ["admin", "tenant_admin", "tenant_user", "user", "callAgent"],
  },
];

export function NavSidebar() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const router = useRouter();
  const { role, username, logout, token } = useAuth();
  const activeSector = (searchParams.get("sector") || "general").trim().toLowerCase();
  const activeChatId = searchParams.get("chat_id");
  const isChatRoute = pathname === "/chat" || pathname.startsWith("/chat/");
  const { conversations, loading } = useConversations(token, activeSector);

  const visible = navItems.filter(
    (item) => role && item.roles.includes(role)
  );

  const startNewChat = () => {
    router.replace(`/chat?new=1&sector=${encodeURIComponent(activeSector)}`);
  };

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

          if (label !== "Chat") {
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
          }

          return (
            <div
              key={href}
              className="space-y-1"
            >
              <Link
                href={`/chat?sector=${encodeURIComponent(activeSector)}`}
                className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                  active
                    ? "bg-white/10 font-medium"
                    : "hover:bg-white/5 text-sidebar-foreground/70 hover:text-sidebar-foreground"
                }`}
              >
                <Icon size={16} />
                {label}
              </Link>

              <div className="ml-6 pl-2 border-l border-sidebar-border/70 space-y-1">
                <button
                  type="button"
                  onClick={startNewChat}
                  className="w-full flex items-center gap-2 px-2 py-1.5 rounded text-xs text-sidebar-foreground/80 hover:bg-white/5 hover:text-sidebar-foreground transition-colors"
                >
                  <Plus size={12} />
                  New chat
                </button>

                {loading && isChatRoute && (
                  <div className="px-2 py-1 text-[11px] text-sidebar-foreground/60">
                    Loading history...
                  </div>
                )}

                {!loading && isChatRoute && conversations.length === 0 && (
                  <div className="px-2 py-1 text-[11px] text-sidebar-foreground/60">
                    No conversations yet
                  </div>
                )}

                {conversations.slice(0, 8).map((conversation) => {
                  const selected = activeChatId === conversation.chat_id;
                  return (
                    <Link
                      key={conversation.chat_id}
                      href={`/chat?chat_id=${conversation.chat_id}&sector=${encodeURIComponent(activeSector)}`}
                      className={`w-full flex items-center gap-1.5 px-2 py-1 rounded text-xs transition-colors ${
                        selected
                          ? "bg-white/10 text-sidebar-foreground"
                          : "text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-white/5"
                      }`}
                    >
                      <ChevronRight size={11} className="shrink-0" />
                      <span className="truncate">{conversation.title || "Untitled"}</span>
                    </Link>
                  );
                })}
              </div>
            </div>
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
