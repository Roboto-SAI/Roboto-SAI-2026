/**
 * Auth tests - RequireAuth redirect and login flows
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { RequireAuth } from '@/components/auth/RequireAuth';
import { useAuthStore } from '@/stores/authStore';

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

describe('RequireAuth', () => {
  it('should redirect to /login when not authenticated', async () => {
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
