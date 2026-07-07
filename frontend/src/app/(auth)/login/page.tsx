import { LoginForm } from "./LoginForm";

export default function LoginPage() {
  return (
    <div className="w-full max-w-md px-4">
      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold tracking-tight">Enterprise AI OS</h1>
        <p className="text-muted-foreground mt-1">Sign in to your account</p>
      </div>
      <LoginForm />
    </div>
  );
}
