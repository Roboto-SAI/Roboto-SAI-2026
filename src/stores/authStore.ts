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

type PersistedAuthState = {
  userId: string | null;
  username: string | null;
  email: string | null;
  avatarUrl: string | null;
  provider: string | null;
  isLoggedIn: boolean;
};

const isRecord = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null;

const coercePersistedAuthState = (value: unknown): PersistedAuthState => {
  if (!isRecord(value)) {
    return {
      userId: null,
      username: null,
      email: null,
      avatarUrl: null,
      provider: null,
      isLoggedIn: false,
    };
  }

  return {
    userId: typeof value.userId === 'string' ? value.userId : null,
    username: typeof value.username === 'string' ? value.username : null,
    email: typeof value.email === 'string' ? value.email : null,
    avatarUrl: typeof value.avatarUrl === 'string' ? value.avatarUrl : null,
    provider: typeof value.provider === 'string' ? value.provider : null,
    isLoggedIn: value.isLoggedIn === true,
  };
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

  loginWithPassword: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;

  // Real backend session auth
  refreshSession: () => Promise<boolean>;
  requestMagicLink: (email: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist<AuthState, [], [], PersistedAuthState>(
    (set) => ({
      userId: null,
      username: null,
      email: null,
      avatarUrl: null,
      provider: null,
      isLoggedIn: false,

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

      register: async (email: string, password: string) => {
        const apiBaseUrl = getApiBaseUrl();
        const url = apiBaseUrl ? `${apiBaseUrl}/api/auth/register` : '/api/auth/register';
        const res = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ email, password }),
        });
        if (!res.ok) {
          const txt = await res.text().catch(() => '');
          throw new Error(txt || 'Registration failed');
        }
      },

      loginWithPassword: async (email: string, password: string) => {
        const apiBaseUrl = getApiBaseUrl();
        const url = apiBaseUrl ? `${apiBaseUrl}/api/auth/login` : '/api/auth/login';
        const res = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ email, password }),
        });
        if (!res.ok) {
          const txt = await res.text().catch(() => '');
          throw new Error(txt || 'Login failed');
        }
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
      version: 2,
      migrate: (persistedState, _version) => {
        const envelope = isRecord(persistedState) ? persistedState : null;
        const rawState = envelope && isRecord(envelope.state) ? envelope.state : persistedState;

        const parsed = coercePersistedAuthState(rawState);
        if (parsed.provider === 'demo') {
          return {
            userId: null,
            username: null,
            email: null,
            avatarUrl: null,
            provider: null,
            isLoggedIn: false,
          };
        }
        return parsed;
      },
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
