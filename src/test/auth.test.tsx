/**
 * Auth tests - RequireAuth redirect and login flows
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { RequireAuth } from '@/components/auth/RequireAuth';
import { useAuthStore } from '@/stores/authStore';

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

describe('RequireAuth', () => {
  it('should redirect to /login when not authenticated', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({ ok: false } as unknown as Response) as unknown as typeof fetch;
    useAuthStore.setState({ isLoggedIn: false }, false);

    render(
      <MemoryRouter initialEntries={['/chat']}>
        <Routes>
          <Route
            path="/chat"
            element={
              <RequireAuth>
                <div>Protected Content</div>
              </RequireAuth>
            }
          />
          <Route path="/login" element={<div>Login Page</div>} />
        </Routes>
      </MemoryRouter>
    );

    // Should redirect to login
    await waitFor(() => {
      expect(screen.getByText('Login Page')).toBeInTheDocument();
    });
  });

  it('should render protected content when authenticated', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
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
    } as unknown as Response) as unknown as typeof fetch;
    useAuthStore.setState({ isLoggedIn: true }, false);

    render(
      <MemoryRouter initialEntries={['/chat']}>
        <Routes>
          <Route
            path="/chat"
            element={
              <RequireAuth>
                <div>Protected Content</div>
              </RequireAuth>
            }
          />
          <Route path="/login" element={<div>Login Page</div>} />
        </Routes>
      </MemoryRouter>
    );

    // Should show protected content
    await waitFor(() => {
      expect(screen.getByText('Protected Content')).toBeInTheDocument();
    });
  });

  it('should not render anything initially when not authenticated', () => {
    globalThis.fetch = vi.fn().mockResolvedValue({ ok: false } as unknown as Response) as unknown as typeof fetch;
    useAuthStore.setState({ isLoggedIn: false }, false);

    render(
      <MemoryRouter initialEntries={['/chat']}>
        <Routes>
          <Route
            path="/chat"
            element={
              <RequireAuth>
                <div>Protected Content</div>
              </RequireAuth>
            }
          />
        </Routes>
      </MemoryRouter>
    );

    // Should not render protected content before redirect
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });
});
