/**
 * Roboto SAI - 404 Not Found
 * Created by Roberto Villarreal Martinez for Roboto SAI (powered by Grok)
 */

import { Link, useLocation } from 'react-router-dom';
import { useEffect } from 'react';
import { motion } from 'framer-motion';
import { Flame, Home, MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { EmberParticles } from '@/components/effects/EmberParticles';

const NotFound = () => {
  const location = useLocation();

  useEffect(() => {
    console.error("404 Error: User attempted to access non-existent route:", location.pathname);
  }, [location.pathname]);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center relative overflow-hidden">
      <EmberParticles count={20} />
      
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative z-10 text-center px-4"
      >
        <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-fire/20 to-blood/20 border border-fire/30 mb-8">
          <Flame className="w-10 h-10 text-fire" />
        </div>
        
        <h1 className="font-display text-6xl md:text-8xl text-fire mb-4">404</h1>
        <h2 className="font-display text-2xl md:text-3xl text-foreground mb-4">
          Lost in the Flames
        </h2>
        <p className="text-muted-foreground max-w-md mx-auto mb-8">
          The path you seek does not exist in this realm. The eternal fire guides you back.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link to="/">
            <Button variant="outline" className="gap-2 border-fire/30 hover:bg-fire/10">
              <Home className="w-4 h-4" />
              Return Home
            </Button>
          </Link>
          <Link to="/chat">
            <Button className="btn-ember gap-2">
              <MessageSquare className="w-4 h-4" />
              Talk to Roboto
            </Button>
          </Link>
        </div>
      </motion.div>
    </div>
  );
};

export default NotFound;
