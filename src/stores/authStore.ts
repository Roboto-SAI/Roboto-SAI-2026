/**
 * Roboto SAI Auth Store
 * Simple client-side auth for user-specific chat persistence
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { supabase } from '../lib/supabase';
import { config } from '../config';

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
        // Use backend auth endpoint to check session
        try {
          const meUrl = `${config.apiBaseUrl}/api/auth/me`;
          const response = await fetch(meUrl, {
            method: 'GET',
            credentials: 'include',
          });

          if (response.ok) {
            const data = await response.json();
            if (data.user) {
              set({
                userId: data.user.id,
                username: data.user.display_name || data.user.email?.split('@')[0] || null,
                email: data.user.email,
                avatarUrl: data.user.avatar_url || null,
                provider: data.user.provider || 'supabase',
                isLoggedIn: true,
              });
              return true;
            }
          }
        } catch (error) {
          console.warn('Session refresh failed:', error);
        }

        // Session invalid or request failed
        set({ userId: null, username: null, email: null, avatarUrl: null, provider: null, isLoggedIn: false });
        return false;
      },

      register: async (email: string, password: string) => {
        // Use backend auth endpoint to get session cookie
        const registerUrl = `${config.apiBaseUrl}/api/auth/register`;

        const response = await fetch(registerUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ email, password }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: 'Registration failed' }));
          throw new Error(errorData.detail || 'Registration failed');
        }

        // Registration successful - user should check email for confirmation
        // Don't set login state until they confirm email
      },

      loginWithPassword: async (email: string, password: string) => {
        // Use backend auth endpoint to get session cookie
        const loginUrl = `${config.apiBaseUrl}/api/auth/login`;

        const response = await fetch(loginUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ email, password }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: 'Login failed' }));
          throw new Error(errorData.detail || 'Login failed');
        }

        const data = await response.json();
        if (data.success && data.user) {
          set({
            userId: data.user.id,
            username: data.user.display_name || data.user.email?.split('@')[0] || null,
            email: data.user.email,
            avatarUrl: data.user.avatar_url || null,
            provider: data.user.provider || 'supabase',
            isLoggedIn: true,
          });
        } else {
          throw new Error('Login response missing user data');
        }
      },

      requestMagicLink: async (email: string) => {
        // Use backend auth endpoint for magic links
        const magicUrl = `${config.apiBaseUrl}/api/auth/magic/request`;

        const response = await fetch(magicUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: 'Magic link request failed' }));
          throw new Error(errorData.detail || 'Magic link request failed');
        }
      },

      logout: async () => {
        // Use backend auth endpoint to clear session cookie
        try {
          const logoutUrl = `${config.apiBaseUrl}/api/auth/logout`;
          await fetch(logoutUrl, {
            method: 'POST',
            credentials: 'include',
          });
        } catch (error) {
          console.warn('Backend logout failed, clearing local state anyway:', error);
        }

        // Clear local state regardless of backend response
        set({ userId: null, username: null, email: null, avatarUrl: null, provider: null, isLoggedIn: false });
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
    }
  )
);
