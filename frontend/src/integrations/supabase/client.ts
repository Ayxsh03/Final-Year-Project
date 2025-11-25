// Stub implementation to replace Supabase client with backend API calls
// This maintains the same export structure to minimize breaking changes

// Mock Supabase client that prevents runtime errors
// All functionality is now handled via backend API endpoints
export const supabase = {
  auth: {
    signInWithPassword: () => Promise.reject(new Error('Use backend API /api/v1/auth/login instead')),
    signUp: () => Promise.reject(new Error('Use backend API /api/v1/auth/register instead')),
    signOut: () => Promise.reject(new Error('Use backend API /api/v1/auth/logout instead')),
    getSession: () => Promise.resolve({ data: { session: null }, error: null }),
    onAuthStateChange: () => ({
      data: { subscription: { unsubscribe: () => { } } }
    })
  },
  from: () => ({
    select: () => Promise.reject(new Error('Use backend API endpoints instead')),
    insert: () => Promise.reject(new Error('Use backend API endpoints instead')),
    update: () => Promise.reject(new Error('Use backend API endpoints instead')),
    delete: () => Promise.reject(new Error('Use backend API endpoints instead')),
  }),
  channel: () => ({
    on: () => ({ subscribe: () => { } }),
  }),
  removeChannel: () => { },
};

// Export type for compatibility
export type SupabaseClient = typeof supabase;
