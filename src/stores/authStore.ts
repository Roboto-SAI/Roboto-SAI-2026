/**
 * Roboto SAI Auth Store
 * Simple client-side auth for user-specific chat persistence
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type AuthUser = {
  id: string;
  email: string;
  display_name?: string | null;
  avatar_url?: string | null;
  provider?: string | null;
};

type MeResponse = {
  user?: AuthUser;
};

const getApiBaseUrl = (): string => {
  const envUrl = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || '';
  const trimmed = envUrl.replace(/\/+$/, '');
  if (!trimmed) return '';
  return trimmed.endsWith('/api') ? trimmed.slice(0, -4) : trimmed;
};

interface AuthState {
  userId: string | null;
  username: string | null;
  email: string | null;
  avatarUrl: string | null;
  provider: string | null;
  isLoggedIn: boolean;

  // Legacy demo login (kept so the current landing page continues to work)
  login: (username: string, email?: string | null) => void;

  // Real backend session auth
  refreshSession: () => Promise<boolean>;
  startGoogleSignIn: () => void;
  requestMagicLink: (email: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      userId: null,
      username: null,
      email: null,
      avatarUrl: null,
      provider: null,
      isLoggedIn: false,

      login: (username: string, email?: string | null) => {
        const userId = username.toLowerCase().replace(/\s+/g, '_').slice(0, 64);
        set({ userId, username, email: email || null, isLoggedIn: true, provider: 'demo' });
      },

      refreshSession: async () => {
        const apiBaseUrl = getApiBaseUrl();
        const url = apiBaseUrl ? `${apiBaseUrl}/api/auth/me` : '/api/auth/me';
        try {
          const res = await fetch(url, { credentials: 'include' });
          if (!res.ok) {
            set({ userId: null, username: null, email: null, avatarUrl: null, provider: null, isLoggedIn: false });
            return false;
          }
          const data = (await res.json()) as MeResponse;
          if (!data.user?.id) {
            set({ userId: null, username: null, email: null, avatarUrl: null, provider: null, isLoggedIn: false });
            return false;
          }
          set({
            userId: data.user.id,
            username: data.user.display_name || data.user.email?.split('@')[0] || null,
            email: data.user.email || null,
            avatarUrl: data.user.avatar_url || null,
            provider: data.user.provider || null,
            isLoggedIn: true,
          });
          return true;
        } catch {
          set({ userId: null, username: null, email: null, avatarUrl: null, provider: null, isLoggedIn: false });
          return false;
        }
      },

      startGoogleSignIn: () => {
        const apiBaseUrl = getApiBaseUrl();
        const url = apiBaseUrl ? `${apiBaseUrl}/api/auth/google/start` : '/api/auth/google/start';
        window.location.href = url;
      },

      requestMagicLink: async (email: string) => {
        const apiBaseUrl = getApiBaseUrl();
        const url = apiBaseUrl ? `${apiBaseUrl}/api/auth/magic/request` : '/api/auth/magic/request';
        const res = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ email }),
        });
        if (!res.ok) {
          const txt = await res.text().catch(() => '');
          throw new Error(txt || 'Magic link request failed');
        }
      },

      logout: async () => {
        const apiBaseUrl = getApiBaseUrl();
        const url = apiBaseUrl ? `${apiBaseUrl}/api/auth/logout` : '/api/auth/logout';
        try {
          await fetch(url, { method: 'POST', credentials: 'include' });
        } finally {
          set({ userId: null, username: null, email: null, avatarUrl: null, provider: null, isLoggedIn: false });
        }
      },
    }),
    {
      name: 'robo-auth',
      partialize: (state) => ({
        userId: state.userId,
        username: state.username,
        email: state.email,
        avatarUrl: state.avatarUrl,
        provider: state.provider,
        isLoggedIn: state.isLoggedIn,
      }),
    }
  )
);
