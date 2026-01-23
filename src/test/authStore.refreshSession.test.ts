import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { useAuthStore } from '@/stores/authStore';

describe('authStore.refreshSession', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    useAuthStore.setState(
      {
        userId: null,
        username: null,
        email: null,
        avatarUrl: null,
        provider: null,
        isLoggedIn: false,
      },
      false
    );
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it('hydrates user state when /api/auth/me returns a user', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        user: {
          id: 'u_123',
          email: 'user@example.com',
          display_name: 'User',
          avatar_url: null,
          provider: 'password',
        },
      }),
    } as unknown as Response);

    globalThis.fetch = fetchMock as unknown as typeof fetch;

    const ok = await useAuthStore.getState().refreshSession();

    expect(ok).toBe(true);
    expect(fetchMock).toHaveBeenCalledWith('/api/auth/me', { credentials: 'include' });

    const state = useAuthStore.getState();
    expect(state.isLoggedIn).toBe(true);
    expect(state.userId).toBe('u_123');
    expect(state.username).toBe('User');
    expect(state.email).toBe('user@example.com');
    expect(state.provider).toBe('password');
  });

  it('clears user state when /api/auth/me returns 401/!ok', async () => {
    useAuthStore.setState(
      {
        isLoggedIn: true,
        userId: 'u_123',
        username: 'User',
        email: 'user@example.com',
        provider: 'password',
      },
      false
    );

    const fetchMock = vi.fn().mockResolvedValue({ ok: false } as unknown as Response);
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    const ok = await useAuthStore.getState().refreshSession();

    expect(ok).toBe(false);

    const state = useAuthStore.getState();
    expect(state.isLoggedIn).toBe(false);
    expect(state.userId).toBeNull();
    expect(state.username).toBeNull();
    expect(state.email).toBeNull();
    expect(state.provider).toBeNull();
  });
});
