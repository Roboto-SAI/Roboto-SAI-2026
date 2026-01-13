/**
 * Roboto SAI Ember Particles Effect
 * Created by Roberto Villarreal Martinez for Roboto SAI (powered by Grok)
 */

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

interface Particle {
  id: number;
  x: number;
  size: number;
  duration: number;
  delay: number;
}

interface EmberParticlesProps {
  count?: number;
  isVentMode?: boolean;
}

export const EmberParticles = ({ count = 20, isVentMode = false }: EmberParticlesProps) => {
  const [particles, setParticles] = useState<Particle[]>([]);

  useEffect(() => {
    const newParticles: Particle[] = [];
    for (let i = 0; i < count; i++) {
      newParticles.push({
        id: i,
        x: Math.random() * 100,
        size: Math.random() * 4 + 2,
        duration: Math.random() * 4 + 3,
        delay: Math.random() * 5,
      });
    }
    setParticles(newParticles);
  }, [count]);

  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
      {particles.map((particle) => (
        <motion.div
          key={particle.id}
          className={`absolute rounded-full ${
            isVentMode 
              ? 'bg-gradient-to-t from-blood to-red-500' 
              : 'bg-gradient-to-t from-fire to-primary'
          }`}
          style={{
            left: `${particle.x}%`,
            width: particle.size,
            height: particle.size,
            filter: `blur(${particle.size / 4}px)`,
          }}
          initial={{ y: '100vh', opacity: 0, scale: 0 }}
          animate={{
            y: '-10vh',
            opacity: [0, 1, 1, 0],
            scale: [0, 1, 1, 0.5],
          }}
          transition={{
            duration: particle.duration,
            delay: particle.delay,
            repeat: Infinity,
            ease: 'easeOut',
          }}
        />
      ))}
    </div>
  );
};
