/**
 * Roboto SAI Typing Indicator Component
 * Created by Roberto Villarreal Martinez for Roboto SAI (powered by Grok)
 */

import { motion } from 'framer-motion';
import { Bot } from 'lucide-react';

export const TypingIndicator = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="flex gap-3"
    >
      {/* Avatar */}
      <div className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center bg-gradient-to-br from-fire/20 to-blood/20 border border-fire/30">
        <Bot className="w-5 h-5 text-fire" />
      </div>

      {/* Typing Bubble */}
      <div className="message-roboto rounded-2xl px-4 py-3 flex items-center gap-2">
        <span className="text-sm text-muted-foreground animate-typing">
          Roboto is thinking
        </span>
        <div className="flex gap-1">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className="w-1.5 h-1.5 rounded-full bg-fire"
              animate={{
                scale: [1, 1.3, 1],
                opacity: [0.5, 1, 0.5],
              }}
              transition={{
                duration: 1,
                repeat: Infinity,
                delay: i * 0.2,
              }}
            />
          ))}
        </div>
      </div>
    </motion.div>
  );
};
