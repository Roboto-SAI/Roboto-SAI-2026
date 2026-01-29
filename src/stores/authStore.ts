/**
 * Roboto SAI Auth Store
 * Simple client-side auth for user-specific chat persistence
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

let supabase: SupabaseClient | null = null;
if (supabaseUrl && supabaseKey) {
  supabase = createClient(supabaseUrl, supabaseKey);
}

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
        if (!supabase) {
          // Demo mode
          set({
            userId: 'demo-user',
            username: 'Demo',
            email: 'demo@example.com',
            avatarUrl: null,
            provider: 'demo',
            isLoggedIn: true,
          });
          return true;
        }
        const { data, error } = await supabase.auth.getSession();
        if (error || !data.session) {
          set({ userId: null, username: null, email: null, avatarUrl: null, provider: null, isLoggedIn: false });
          return false;
        }
        const user = data.session.user;
        set({
          userId: user.id,
          username: user.user_metadata?.display_name || user.email?.split('@')[0] || null,
          email: user.email || null,
          avatarUrl: user.user_metadata?.avatar_url || null,
          provider: user.app_metadata?.provider || null,
          isLoggedIn: true,
        });
        return true;
      },

      register: async (email: string, password: string) => {
        if (!supabase) {
          // Demo mode, just set
          set({
            userId: 'demo-user',
            username: email.split('@')[0],
            email,
            avatarUrl: null,
            provider: 'demo',
            isLoggedIn: true,
          });
          return;
        }
        const { error } = await supabase.auth.signUp({ email, password });
        if (error) throw error;
      },

      loginWithPassword: async (email: string, password: string) => {
        if (!supabase) {
          // Demo mode
          set({
            userId: 'demo-user',
            username: email.split('@')[0],
            email,
            avatarUrl: null,
            provider: 'demo',
            isLoggedIn: true,
          });
          return;
        }
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
      },

      requestMagicLink: async (email: string) => {
        if (!supabase) throw new Error('Supabase not configured');
        const { error } = await supabase.auth.signInWithOtp({ email });
        if (error) throw error;
      },

      logout: async () => {
        if (supabase) {
          await supabase.auth.signOut();
        }
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
