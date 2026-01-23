import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthForm } from '@/components/auth/AuthForm';
describe('AuthForm UI', () => {
  it('does not show Google or Demo auth, and supports register toggle', () => {
    render(
      <MemoryRouter>
        <AuthForm onSubmit={() => {}} initialMode="login" />
      </MemoryRouter>
    );

    expect(screen.queryByRole('button', { name: /continue with google/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /demo login/i })).not.toBeInTheDocument();

    expect(screen.getByRole('button', { name: /password/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /magic/i })).toBeInTheDocument();

    expect(screen.getByRole('button', { name: /don't have an account\? register/i })).toBeInTheDocument();
  });
});
