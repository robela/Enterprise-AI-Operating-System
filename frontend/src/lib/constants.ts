export const APP_NAME = "Enterprise AI OS";

export const ROLE_PERMISSIONS = {
  admin: ["view_dashboard", "manage_users", "manage_documents", "view_audit", "view_chat"],
  user: ["view_chat"],
  callAgent: ["view_chat"],
} as const;

export const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8060";
