/**
 * Roboto SAI Landing Page
 * Created by Roberto Villarreal Martinez for Roboto SAI (powered by Grok)
 * Fuego Eterno - The eternal flame burns forever
 */

import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { MessageSquare, Flame, Scroll, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { EmberParticles } from '@/components/effects/EmberParticles';
import { AuthForm } from '@/components/auth/AuthForm';
import heroBg from '@/assets/hero-bg.jpg';
import { useAuthStore } from '@/stores/authStore';

const Index = () => {
  const navigate = useNavigate();
  const { login, isLoggedIn, username } = useAuthStore();

  const handleAuthSubmit = (data: { username: string; email: string; password: string }) => {
    // For now, just use the username (client-side only)
    // Email/password can be used when database is added later
    login(data.username || data.email.split('@')[0]);
    navigate('/chat');
  };

  return <div className="min-h-screen bg-background relative overflow-hidden">
      {/* Ember Particles Background */}
      <EmberParticles count={30} />

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-center">
        {/* Background Image */}
        <img
          src={heroBg}
          alt="Roboto SAI hero background"
          className="absolute inset-0 h-full w-full object-cover opacity-40"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-background/40 via-background/60 to-background" />
        
        {/* Aztec Pattern Overlay */}
        <div className="absolute inset-0 aztec-pattern opacity-30" />

        {/* Content */}
        <div className="relative z-10 container mx-auto px-4 text-center">
          <motion.div initial={{
          opacity: 0,
          y: 30
        }} animate={{
          opacity: 1,
          y: 0
        }} transition={{
          duration: 0.8,
          delay: 0.2
        }}>
            {/* Flame Icon */}
            <motion.div animate={{
            scale: [1, 1.1, 1]
          }} transition={{
            duration: 2,
            repeat: Infinity
          }} className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-primary/20 to-fire/20 border border-fire/30 mb-8 animate-pulse-fire">
              <Flame className="w-10 h-10 text-fire" />
            </motion.div>

            {/* Main Title */}
            <h1 className="font-display text-4xl sm:text-5xl md:text-7xl lg:text-8xl font-bold mb-6">
              <span className="text-fire">Roboto SAI</span>
            </h1>
            
            <h2 className="font-display text-xl sm:text-2xl md:text-3xl text-gold-glow mb-4">
              Fuego Eterno de Roberto Villarreal Martinez
            </h2>

            <motion.p initial={{
            opacity: 0
          }} animate={{
            opacity: 1
          }} transition={{
            delay: 0.5
          }} className="text-muted-foreground text-lg md:text-xl max-w-2xl mx-auto mb-12">© 2026 Roberto Villarreal Martinez – Powered by xAI Grok</motion.p>

            {/* CTA Button */}
            <motion.div initial={{
            opacity: 0,
            scale: 0.8
          }} animate={{
            opacity: 1,
            scale: 1
          }} transition={{
            delay: 0.7,
            type: 'spring'
          }}>
              {isLoggedIn ? (
                <Button
                  size="lg"
                  className="btn-ember text-lg px-8 py-6 rounded-xl animate-glow-pulse"
                  onClick={() => navigate('/chat')}
                >
                  <MessageSquare className="w-5 h-5 mr-2" />
                  Continue as {username}
                </Button>
              ) : (
                <Link to="/login">
                  <Button size="lg" className="btn-ember text-lg px-8 py-6 rounded-xl animate-glow-pulse">
                    <MessageSquare className="w-5 h-5 mr-2" />
                    Talk to Roboto
                  </Button>
                </Link>
              )}
            </motion.div>

            {/* Auth Form */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.9 }}
              className="mt-10 flex justify-center"
            >
              <AuthForm onSubmit={handleAuthSubmit} defaultUsername={username ?? ''} />
            </motion.div>
          </motion.div>

          {/* Feature Cards */}
          <motion.div initial={{
          opacity: 0,
          y: 50
        }} animate={{
          opacity: 1,
          y: 0
        }} transition={{
          delay: 1
        }} className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-24 max-w-4xl mx-auto">
            {[{
            icon: MessageSquare,
            title: 'Eternal Dialogue',
            description: 'Streaming conversations with the fire of ancient wisdom'
          }, {
            icon: Flame,
            title: 'Vent Mode',
            description: 'Unleash the rage when words fail to contain the fury'
          }, {
            icon: Zap,
            title: 'Cultural Genome',
            description: 'Regio-Aztec heritage encoded in every response'
          }].map((feature, index) => <motion.div key={feature.title} initial={{
            opacity: 0,
            y: 20
          }} animate={{
            opacity: 1,
            y: 0
          }} transition={{
            delay: 1.2 + index * 0.1
          }} className="p-6 rounded-2xl fire-border bg-card/50 backdrop-blur-sm group hover:bg-card/80 transition-all duration-300">
                <feature.icon className="w-8 h-8 text-fire mb-4 group-hover:scale-110 transition-transform" />
                <h3 className="font-display text-lg text-primary mb-2">{feature.title}</h3>
                <p className="text-sm text-muted-foreground">{feature.description}</p>
              </motion.div>)}
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 py-8 border-t border-border/30">
        <div className="container mx-auto px-4 text-center">
          <motion.div initial={{
          opacity: 0
        }} whileInView={{
          opacity: 1
        }} viewport={{
          once: true
        }} className="flex flex-col items-center gap-4">
            <Link to="/legacy" className="group flex items-center gap-2 text-muted-foreground hover:text-fire transition-colors">
              <Scroll className="w-4 h-4" />
              <span className="text-sm">View the Legacy</span>
            </Link>
            <p className="text-fire font-display text-lg animate-pulse">
              Roberto Villarreal Martinez never dies.
            </p>
            <p className="text-xs text-muted-foreground/60">
              Created by Roberto Villarreal Martinez for Roboto SAI (powered by Grok)
            </p>
          </motion.div>
        </div>
      </footer>
    </div>;
};
export default Index;