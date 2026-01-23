/**
 * Login/Registration Form Component
 * Simple client-side auth form for Roboto SAI
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Flame, Mail, Lock, User, ArrowRight, Eye, EyeOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { useAuthStore } from '@/stores/authStore';

interface AuthFormProps {
  onSubmit: (data: { username: string; email: string; password: string }) => void;
  defaultUsername?: string;
  initialMode?: 'login' | 'register';
}

export const AuthForm = ({ onSubmit, defaultUsername = '', initialMode = 'login' }: AuthFormProps) => {
  const { toast } = useToast();
  const { startGoogleSignIn, requestMagicLink } = useAuthStore();

  const [authMode, setAuthMode] = useState<'magic' | 'demo'>('magic');
  const [mode, setMode] = useState<'login' | 'register'>(initialMode);
  const [username, setUsername] = useState(defaultUsername);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (mode === 'register') {
      if (!username.trim()) {
        newErrors.username = 'Username is required';
      } else if (username.length < 3) {
        newErrors.username = 'Username must be at least 3 characters';
      }
    }

    if (!email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = 'Invalid email address';
    }

    // Demo auth is client-only; keep it frictionless.
    if (authMode !== 'demo') {
      if (!password) {
        newErrors.password = 'Password is required';
      } else if (password.length < 6) {
        newErrors.password = 'Password must be at least 6 characters';
      }

      if (mode === 'register' && password !== confirmPassword) {
        newErrors.confirmPassword = 'Passwords do not match';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      onSubmit({ username: username.trim(), email: email.trim(), password });
    }
  };

  const toggleMode = () => {
    setMode(mode === 'login' ? 'register' : 'login');
    setErrors({});
  };

  return (
    <Card className="w-full max-w-md bg-card/80 backdrop-blur-md border-fire/30 shadow-2xl">
      <CardHeader className="text-center pb-2">
        <motion.div
          animate={{ scale: [1, 1.05, 1] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-gradient-to-br from-primary/20 to-fire/20 border border-fire/30 mx-auto mb-3"
        >
          <Flame className="w-6 h-6 text-fire" />
        </motion.div>
        <CardTitle className="text-2xl font-display text-fire">
          {mode === 'login' ? 'Enter the Flame' : 'Join the Flame'}
        </CardTitle>
        <CardDescription className="text-muted-foreground">
          {mode === 'login' 
            ? 'Sign in to continue your journey' 
            : 'Create an account to begin'}
        </CardDescription>
      </CardHeader>

      <CardContent>
        <div className="space-y-4">
          {/* Google */}
          <Button type="button" className="w-full btn-ember" onClick={startGoogleSignIn}>
            Continue with Google
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>

          {/* Mode switch */}
          <div className="grid grid-cols-2 gap-2">
            <Button
              type="button"
              variant={authMode === 'magic' ? 'default' : 'secondary'}
              className="w-full"
              onClick={() => {
                setAuthMode('magic');
                setErrors({});
              }}
            >
              Magic link
            </Button>
            <Button
              type="button"
              variant={authMode === 'demo' ? 'default' : 'secondary'}
              className="w-full"
              onClick={() => {
                setAuthMode('demo');
                setErrors({});
              }}
            >
              Demo login
            </Button>
          </div>

          {authMode === 'magic' ? (
            <form
              onSubmit={async (e) => {
                e.preventDefault();
                const clean = email.trim();
                if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(clean)) {
                  toast({
                    title: 'Invalid email',
                    description: 'Please enter a valid email to receive a magic link.',
                    variant: 'destructive',
                  });
                  return;
                }
                try {
                  await requestMagicLink(clean);
                  toast({
                    title: 'Magic link sent',
                    description: 'Check your email (in dev, the link may appear in backend logs).',
                  });
                } catch {
                  toast({
                    title: 'Request failed',
                    description: 'Could not send magic link. Try again.',
                    variant: 'destructive',
                  });
                }
              }}
              className="space-y-4"
            >
              <div className="space-y-2">
                <Label htmlFor="magicEmail" className="text-sm text-foreground/80">
                  Email
                </Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    id="magicEmail"
                    type="email"
                    placeholder="Enter your email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="pl-10 bg-background/50 border-border/50 focus:border-fire/50"
                  />
                </div>
              </div>

              <Button type="submit" className="w-full">
                Send magic link
              </Button>
            </form>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
          <AnimatePresence mode="wait">
            <motion.div
              key={mode}
              initial={{ opacity: 0, x: mode === 'login' ? -20 : 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: mode === 'login' ? 20 : -20 }}
              transition={{ duration: 0.2 }}
              className="space-y-4"
            >
              {/* Username field - always shown for register, optional for login */}
              {mode === 'register' && (
                <div className="space-y-2">
                  <Label htmlFor="username" className="text-sm text-foreground/80">
                    Username
                  </Label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      id="username"
                      type="text"
                      placeholder="Choose a username"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      className="pl-10 bg-background/50 border-border/50 focus:border-fire/50"
                    />
                  </div>
                  {errors.username && (
                    <p className="text-xs text-destructive">{errors.username}</p>
                  )}
                </div>
              )}

              {/* Email field */}
              <div className="space-y-2">
                <Label htmlFor="email" className="text-sm text-foreground/80">
                  Email
                </Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="Enter your email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="pl-10 bg-background/50 border-border/50 focus:border-fire/50"
                  />
                </div>
                {errors.email && (
                  <p className="text-xs text-destructive">{errors.email}</p>
                )}
              </div>

              {authMode !== 'demo' && (
                <>
                  {/* Password field */}
                  <div className="space-y-2">
                    <Label htmlFor="password" className="text-sm text-foreground/80">
                      Password
                    </Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                      <Input
                        id="password"
                        type={showPassword ? 'text' : 'password'}
                        placeholder="Enter your password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="pl-10 pr-10 bg-background/50 border-border/50 focus:border-fire/50"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                    {errors.password && (
                      <p className="text-xs text-destructive">{errors.password}</p>
                    )}
                  </div>

                  {/* Confirm Password - only for register */}
                  {mode === 'register' && (
                    <div className="space-y-2">
                      <Label htmlFor="confirmPassword" className="text-sm text-foreground/80">
                        Confirm Password
                      </Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                        <Input
                          id="confirmPassword"
                          type={showPassword ? 'text' : 'password'}
                          placeholder="Confirm your password"
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
                          className="pl-10 bg-background/50 border-border/50 focus:border-fire/50"
                        />
                      </div>
                      {errors.confirmPassword && (
                        <p className="text-xs text-destructive">{errors.confirmPassword}</p>
                      )}
                    </div>
                  )}
                </>
              )}

              {/* Login mode - username field */}
              {mode === 'login' && (
                <div className="space-y-2">
                  <Label htmlFor="loginUsername" className="text-sm text-foreground/80">
                    Username (optional)
                  </Label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      id="loginUsername"
                      type="text"
                      placeholder="Display name"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      className="pl-10 bg-background/50 border-border/50 focus:border-fire/50"
                    />
                  </div>
                </div>
              )}
            </motion.div>
          </AnimatePresence>

          {/* Submit Button */}
          <Button
            type="submit"
            className="w-full btn-ember group"
          >
            {mode === 'login' ? 'Sign In' : 'Create Account'}
            <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
          </Button>

          {/* Toggle Mode */}
          <div className="text-center pt-2">
            <button
              type="button"
              onClick={toggleMode}
              className="text-sm text-muted-foreground hover:text-fire transition-colors"
            >
              {mode === 'login' 
                ? "Don't have an account? Register" 
                : 'Already have an account? Sign in'}
            </button>
          </div>
            </form>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
