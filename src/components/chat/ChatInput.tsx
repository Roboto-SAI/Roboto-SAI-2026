/**
 * Roboto SAI Chat Input Component
 * Created by Roberto Villarreal Martinez for Roboto SAI (powered by Grok)
 */

import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Send, Flame } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  ventMode?: boolean;
  onVentToggle?: () => void;
}

export const ChatInput = ({ onSend, disabled, ventMode, onVentToggle }: ChatInputProps) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
    }
  }, [input]);

  const handleSubmit = () => {
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-4 border-t border-border/50 bg-card/80 backdrop-blur-sm"
    >
      <div className="max-w-4xl mx-auto flex gap-3 items-end">
        {/* Vent Mode Toggle */}
        <Button
          variant="ghost"
          size="icon"
          onClick={onVentToggle}
          className={`flex-shrink-0 transition-all duration-300 ${
            ventMode 
              ? 'bg-blood/20 text-blood hover:bg-blood/30 animate-pulse' 
              : 'text-muted-foreground hover:text-fire hover:bg-fire/10'
          }`}
          title={ventMode ? 'Disable Vent Mode' : 'Enable Vent Mode'}
        >
          <Flame className="w-5 h-5" />
        </Button>

        {/* Input Area */}
        <div className="flex-1 relative">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Speak to Roboto..."
            disabled={disabled}
            className="min-h-[48px] max-h-[150px] resize-none pr-12 bg-muted/50 border-border/50 focus:border-primary/50 focus:ring-1 focus:ring-primary/30 placeholder:text-muted-foreground/50 text-foreground"
            rows={1}
          />
        </div>

        {/* Send Button */}
        <Button
          onClick={handleSubmit}
          disabled={!input.trim() || disabled}
          className="flex-shrink-0 btn-ember h-12 w-12 p-0 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Send className="w-5 h-5" />
        </Button>
      </div>
    </motion.div>
  );
};
