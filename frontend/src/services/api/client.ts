import axios, { type AxiosError } from "axios";

// Use the frontend's same-origin API proxy by default so client bundles do not
// bake in a deployment-specific backend host at build time.
const BACKEND_URL =
  typeof window === "undefined" ? process.env.NEXT_PUBLIC_BACKEND_URL?.trim() || "" : "";

export const apiClient = axios.create({
  baseURL: BACKEND_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

// Attach JWT from localStorage on every request
apiClient.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("token");
    const tenantId = localStorage.getItem("tenant_id");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    if (tenantId) {
      config.headers["X-Tenant-ID"] = tenantId;
    }
  }
  return config;
});

// Handle 401 globally — redirect to login
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const isLoginRequest = error.config?.url?.includes("/api/v1/auth/token");
    if (error.response?.status === 401 && !isLoginRequest && typeof window !== "undefined") {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);
