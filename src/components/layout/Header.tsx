/**
 * Roboto SAI Header Component
 * Created by Roberto Villarreal Martinez for Roboto SAI (powered by Grok)
 */

import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Flame, Skull, Home, MessageSquare, Scroll } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useChatStore } from '@/stores/chatStore';

export const Header = () => {
  const location = useLocation();
  const { ventMode, currentTheme } = useChatStore();

  const navItems = [
    { path: '/', icon: Home, label: 'Home' },
    { path: '/chat', icon: MessageSquare, label: 'Chat' },
    { path: '/legacy', icon: Scroll, label: 'Legacy' },
  ];

  return (
    <motion.header
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      className={`fixed top-0 left-0 right-0 z-50 border-b backdrop-blur-md ${
        ventMode 
          ? 'bg-blood/10 border-blood/30' 
          : 'bg-background/80 border-border/50'
      }`}
    >
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 group">
          <div className={`p-2 rounded-lg transition-all duration-300 ${
            ventMode 
              ? 'bg-blood/20' 
              : 'bg-gradient-to-br from-primary/20 to-fire/20 group-hover:from-primary/30 group-hover:to-fire/30'
          }`}>
            {ventMode ? (
              <Skull className="w-6 h-6 text-blood" />
            ) : (
              <Flame className="w-6 h-6 text-fire" />
            )}
          </div>
          <span className="font-display font-bold text-lg text-fire hidden sm:block">
            Roboto SAI
          </span>
        </Link>

        {/* Theme Display */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-muted/50 border border-border/30">
          <div className={`w-2 h-2 rounded-full ${ventMode ? 'bg-blood animate-pulse' : 'bg-fire'}`} />
          <span className="text-xs text-muted-foreground font-medium">
            {ventMode ? 'VENT MODE ACTIVE' : currentTheme}
          </span>
        </div>

        {/* Navigation */}
        <nav className="flex items-center gap-1">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link key={item.path} to={item.path}>
                <Button
                  variant="ghost"
                  size="sm"
                  className={`gap-2 transition-all duration-300 ${
                    isActive
                      ? ventMode
                        ? 'bg-blood/20 text-blood'
                        : 'bg-primary/10 text-primary'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  <item.icon className="w-4 h-4" />
                  <span className="hidden sm:inline">{item.label}</span>
                </Button>
              </Link>
            );
          })}
        </nav>
      </div>
    </motion.header>
  );
};
