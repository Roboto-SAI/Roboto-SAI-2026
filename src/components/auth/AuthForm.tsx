/**
 * Login/Registration Form Component
 * Simple client-side auth form for Roboto SAI
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Flame, Mail, Lock, User, ArrowRight, Eye, EyeOff } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { useAuthStore } from '@/stores/authStore';

const isValidEmail = (value: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());

type AuthMode = 'password' | 'magic';
type FormMode = 'login' | 'register';
type ValidationErrors = Record<string, string>;

const validatePasswordForm = (params: {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
  mode: FormMode;
}): ValidationErrors => {
  const newErrors: ValidationErrors = {};

  const cleanUsername = params.username.trim();
  if (cleanUsername && cleanUsername.length < 3) {
    newErrors.username = 'Username must be at least 3 characters';
  }

  if (!params.email.trim()) {
    newErrors.email = 'Email is required';
  } else if (!isValidEmail(params.email)) {
    newErrors.email = 'Invalid email address';
  }

  if (!params.password) {
    newErrors.password = 'Password is required';
  } else if (params.password.length < 6) {
    newErrors.password = 'Password must be at least 6 characters';
  }

  if (params.mode === 'register' && params.password !== params.confirmPassword) {
    newErrors.confirmPassword = 'Passwords do not match';
  }

  return newErrors;
};

const MagicLinkForm = (props: { email: string; onEmailChange: (value: string) => void }) => {
  const { toast } = useToast();
  const { requestMagicLink } = useAuthStore();

  const handleMagicSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const clean = props.email.trim();
    if (!isValidEmail(clean)) {
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
  };

  return (
    <form onSubmit={handleMagicSubmit} className="space-y-4">
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
            value={props.email}
            onChange={(e) => props.onEmailChange(e.target.value)}
            className="pl-10 bg-background/50 border-border/50 focus:border-fire/50"
          />
        </div>
      </div>

      <Button type="submit" className="w-full">
        Send magic link
      </Button>

      <p className="text-xs text-muted-foreground text-center">
        Magic links work for both sign-in and sign-up.
      </p>
    </form>
  );
};

const PasswordForm = (props: {
  mode: FormMode;
  username: string;
  setUsername: (value: string) => void;
  email: string;
  setEmail: (value: string) => void;
  password: string;
  setPassword: (value: string) => void;
  confirmPassword: string;
  setConfirmPassword: (value: string) => void;
  showPassword: boolean;
  setShowPassword: (value: boolean) => void;
  errors: ValidationErrors;
  setErrors: (value: ValidationErrors) => void;
  onSubmit: (data: { username: string; email: string; password: string }) => void;
  onToggleMode: () => void;
}) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const nextErrors = validatePasswordForm({
      username: props.username,
      email: props.email,
      password: props.password,
      confirmPassword: props.confirmPassword,
      mode: props.mode,
    });
    props.setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;
    props.onSubmit({
      username: props.username.trim(),
      email: props.email.trim(),
      password: props.password,
    });
  };

  const toggleMode = () => {
    props.setErrors({});
    props.onToggleMode();
  };

  const submitLabel = props.mode === 'login' ? 'Sign In' : 'Create Account';

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <AnimatePresence mode="wait">
        <motion.div
          key={props.mode}
          initial={{ opacity: 0, x: props.mode === 'login' ? -20 : 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: props.mode === 'login' ? 20 : -20 }}
          transition={{ duration: 0.2 }}
          className="space-y-4"
        >
          <div className="space-y-2">
            <Label htmlFor="username" className="text-sm text-foreground/80">
              Username (optional)
            </Label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                id="username"
                type="text"
                placeholder="Display name"
                value={props.username}
                onChange={(e) => props.setUsername(e.target.value)}
                className="pl-10 bg-background/50 border-border/50 focus:border-fire/50"
              />
            </div>
            {props.errors.username && <p className="text-xs text-destructive">{props.errors.username}</p>}
          </div>

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
                value={props.email}
                onChange={(e) => props.setEmail(e.target.value)}
                className="pl-10 bg-background/50 border-border/50 focus:border-fire/50"
              />
            </div>
            {props.errors.email && <p className="text-xs text-destructive">{props.errors.email}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="password" className="text-sm text-foreground/80">
              Password
            </Label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                id="password"
                type={props.showPassword ? 'text' : 'password'}
                placeholder="Enter your password"
                value={props.password}
                onChange={(e) => props.setPassword(e.target.value)}
                className="pl-10 pr-10 bg-background/50 border-border/50 focus:border-fire/50"
              />
              <button
                type="button"
                onClick={() => props.setShowPassword(!props.showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              >
                {props.showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            {props.errors.password && <p className="text-xs text-destructive">{props.errors.password}</p>}
          </div>

          {props.mode === 'register' && (
            <div className="space-y-2">
              <Label htmlFor="confirmPassword" className="text-sm text-foreground/80">
                Confirm Password
              </Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  id="confirmPassword"
                  type={props.showPassword ? 'text' : 'password'}
                  placeholder="Confirm your password"
                  value={props.confirmPassword}
                  onChange={(e) => props.setConfirmPassword(e.target.value)}
                  className="pl-10 bg-background/50 border-border/50 focus:border-fire/50"
                />
              </div>
              {props.errors.confirmPassword && (
                <p className="text-xs text-destructive">{props.errors.confirmPassword}</p>
              )}
            </div>
          )}
        </motion.div>
      </AnimatePresence>

      <AnimatePresence mode="wait">
        <motion.div
          key={`${props.mode}-password`}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ duration: 0.15 }}
        >
          <Button type="submit" className="w-full btn-ember group">
            {submitLabel}
            <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
          </Button>
        </motion.div>
      </AnimatePresence>

      <div className="text-center pt-2">
        <button
          type="button"
          onClick={toggleMode}
          className="text-sm text-muted-foreground hover:text-fire transition-colors"
        >
          {props.mode === 'login' ? "Don't have an account? Register" : 'Already have an account? Sign in'}
        </button>
      </div>
    </form>
  );
};

interface AuthFormProps {
  onSubmit: (data: { username: string; email: string; password: string }) => void;
  defaultUsername?: string;
  initialMode?: 'login' | 'register';
}

export const AuthForm = ({ onSubmit, defaultUsername = '', initialMode = 'login' }: AuthFormProps) => {
  const navigate = useNavigate();
  const [authMode, setAuthMode] = useState<AuthMode>('password');
  const mode: FormMode = initialMode;
  const [username, setUsername] = useState(defaultUsername);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const resetPasswordFields = () => {
    setPassword('');
    setConfirmPassword('');
  };

  const switchAuthMode = (next: 'password' | 'magic') => {
    setAuthMode(next);
    setErrors({});
    resetPasswordFields();
  };

  const handleToggleMode = () => {
    navigate(mode === 'login' ? '/register' : '/login');
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
          {/* Mode switch */}
          <div className="grid grid-cols-2 gap-2">
            <Button
              type="button"
              variant={authMode === 'password' ? 'default' : 'secondary'}
              className="w-full"
              onClick={() => switchAuthMode('password')}
            >
              Password
            </Button>
            <Button
              type="button"
              variant={authMode === 'magic' ? 'default' : 'secondary'}
              className="w-full"
              onClick={() => switchAuthMode('magic')}
            >
              Magic
            </Button>
          </div>

          {authMode === 'magic' ? (
            <MagicLinkForm email={email} onEmailChange={setEmail} />
          ) : (
            <PasswordForm
              mode={mode}
              username={username}
              setUsername={setUsername}
              email={email}
              setEmail={setEmail}
              password={password}
              setPassword={setPassword}
              confirmPassword={confirmPassword}
              setConfirmPassword={setConfirmPassword}
              showPassword={showPassword}
              setShowPassword={setShowPassword}
              errors={errors}
              setErrors={setErrors}
              onSubmit={onSubmit}
              onToggleMode={handleToggleMode}
            />
          )}
        </div>
      </CardContent>
    </Card>
  );
};
