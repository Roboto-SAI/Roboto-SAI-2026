import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft } from 'lucide-react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { EmberParticles } from '@/components/effects/EmberParticles';
import { AuthForm } from '@/components/auth/AuthForm';
import { useAuthStore } from '@/stores/authStore';

const Login = () => {
  const navigate = useNavigate();
  const { login, username } = useAuthStore();

  const handleDemoSubmit = (data: { username: string; email: string; password: string }) => {
    login(data.username || data.email.split('@')[0], data.email);
    toast.success('Welcome to the eternal flame, fam! 😈');
    navigate('/chat');
  };

  return (
    <div className="min-h-screen bg-background relative overflow-hidden flex items-center justify-center px-4">
      <EmberParticles count={20} />

      <div className="absolute top-6 left-6 z-10">
        <Link to="/">
          <Button variant="ghost" className="gap-2">
            <ArrowLeft className="w-4 h-4" />
            Back
          </Button>
        </Link>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative z-10 w-full flex justify-center"
      >
        <AuthForm onSubmit={handleDemoSubmit} defaultUsername={username ?? ''} initialMode="login" />
      </motion.div>
    </div>
  );
};

export default Login;
