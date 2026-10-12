"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/utils/auth";
import { toast } from "sonner";
import axios from "axios";

const loginSchema = z.object({
  username: z.string().email("Enter the email address used when the account was created"),
  password: z.string().min(1, "Password is required"),
  tenantId: z.string().min(1, "Tenant is required"),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginForm() {
  const { login } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      tenantId: "default",
    },
  });

  useEffect(() => {
    const tenantFromQuery = searchParams.get("tenant");
    if (tenantFromQuery) {
      setValue("tenantId", tenantFromQuery);
    }
  }, [searchParams, setValue]);

  const onSubmit = async (data: LoginFormData) => {
    try {
      await login(data.username, data.password, data.tenantId);
      router.push("/chat");
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const message = error.response?.data?.message;
        if (typeof message === "string") {
          toast.error(message);
          return;
        }
      }

      toast.error("Unable to sign in. Check your email, password, and tenant.");
    }
  };

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="bg-card border rounded-lg p-8 shadow-sm space-y-4"
    >
      <div className="space-y-1">
        <label htmlFor="username" className="text-sm font-medium">
          Email
        </label>
        <input
          id="username"
          type="email"
          autoComplete="email"
          className="w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          {...register("username")}
        />
        {errors.username && (
          <p className="text-destructive text-xs">{errors.username.message}</p>
        )}
      </div>

      <div className="space-y-1">
        <label htmlFor="tenantId" className="text-sm font-medium">
          Tenant
        </label>
        <input
          id="tenantId"
          type="text"
          autoComplete="organization"
          className="w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          {...register("tenantId")}
        />
        {errors.tenantId && (
          <p className="text-destructive text-xs">{errors.tenantId.message}</p>
        )}
      </div>

      <div className="space-y-1">
        <label htmlFor="password" className="text-sm font-medium">
          Password
        </label>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          className="w-full border rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          {...register("password")}
        />
        {errors.password && (
          <p className="text-destructive text-xs">{errors.password.message}</p>
        )}
      </div>

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full bg-primary text-primary-foreground rounded-md py-2 text-sm font-medium hover:opacity-90 disabled:opacity-60 transition-opacity"
      >
        {isSubmitting ? "Signing in…" : "Sign in"}
      </button>
    </form>
  );
}
