import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { Skeleton } from "@/components/ui/skeleton";

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
  const { user, loading } = useAuth();
  const [backendAuthed, setBackendAuthed] = useState<boolean | null>(null);

  // If no Supabase session, check backend SSO session
  useEffect(() => {
    const checkBackendSession = async () => {
      if (loading) return;
      if (user) {
        setBackendAuthed(false); // not needed when Supabase user exists
        return;
      }
      try {
        const res = await fetch("/api/v1/user", { credentials: "include" });
        if (res.ok) {
          setBackendAuthed(true);
        } else {
          setBackendAuthed(false);
        }
      } catch (_e) {
        setBackendAuthed(false);
      }
    };
    checkBackendSession();
  }, [user, loading]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background p-6">
        <div className="space-y-4">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-32 w-full" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
          </div>
        </div>
      </div>
    );
  }

  if (!user) {
    // While checking backend session, render skeleton
    if (backendAuthed === null) {
      return (
        <div className="min-h-screen bg-background p-6">
          <div className="space-y-4">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-32 w-full" />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-24 w-full" />
            </div>
          </div>
        </div>
      );
    }

    // If backend session exists, allow access
    if (backendAuthed) {
      return <>{children}</>;
    }

    // Neither Supabase nor backend session: go to /auth
    return <Navigate to="/auth" replace />;
  }

  return <>{children}</>;
};