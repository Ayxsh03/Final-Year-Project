import { useState, useEffect } from "react";

interface User {
  id: string;
  email: string;
  name?: string;
  role?: string;
  auth_provider?: string;
}

export const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check backend session on mount
    const checkAuth = async () => {
      try {
        const response = await fetch('/api/v1/user', {
          credentials: 'include', // Include cookies
        });

        if (response.ok) {
          const userData = await response.json();
          setUser(userData);
        } else {
          setUser(null);
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const signOut = async () => {
    try {
      await fetch('/logout', {
        method: 'GET',
        credentials: 'include',
      });
      setUser(null);
      window.location.href = '/auth';
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return {
    user,
    session: user ? { user } : null, // Maintain compatibility
    loading,
    signOut,
  };
};