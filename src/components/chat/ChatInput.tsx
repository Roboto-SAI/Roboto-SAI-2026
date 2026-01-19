/**
 * Roboto SAI Chat Input Component
 * Created by Roberto Villarreal Martinez for Roboto SAI (powered by Grok)
 */

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Flame, Paperclip, X, Mic, MicOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import type { FileAttachment } from '@/stores/chatStore';

interface ChatInputProps {
  onSend: (message: string, attachments?: FileAttachment[]) => void;
  disabled?: boolean;
  ventMode?: boolean;
  onVentToggle?: () => void;
  voiceMode?: boolean;
  onVoiceToggle?: () => void;
  isVoiceActive?: boolean;
}

export const ChatInput = ({ 
  onSend, 
  disabled, 
  ventMode, 
  onVentToggle,
  voiceMode,
  onVoiceToggle,
  isVoiceActive 
}: ChatInputProps) => {
  const [input, setInput] = useState('');
  const [attachments, setAttachments] = useState<FileAttachment[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
    }
  }, [input]);

  const handleSubmit = () => {
    if ((input.trim() || attachments.length > 0) && !disabled) {
      onSend(input.trim(), attachments.length > 0 ? attachments : undefined);
      setInput('');
      setAttachments([]);
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

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    const newAttachments: FileAttachment[] = [];
    
    Array.from(files).forEach((file) => {
      const attachment: FileAttachment = {
        id: crypto.randomUUID(),
        name: file.name,
        type: file.type,
        size: file.size,
        url: URL.createObjectURL(file),
      };
      newAttachments.push(attachment);
    });

    setAttachments(prev => [...prev, ...newAttachments]);
    
    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removeAttachment = (id: string) => {
    setAttachments(prev => {
      const attachment = prev.find(a => a.id === id);
      if (attachment) {
        URL.revokeObjectURL(attachment.url);
      }
      return prev.filter(a => a.id !== id);
    });
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-4 border-t border-border/50 bg-card/80 backdrop-blur-sm"
    >
      {/* Attachments Preview */}
      <AnimatePresence>
        {attachments.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="max-w-4xl mx-auto mb-3"
          >
            <div className="flex flex-wrap gap-2">
              {attachments.map((attachment) => (
                <motion.div
                  key={attachment.id}
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  exit={{ scale: 0 }}
                  className="relative group bg-muted/50 rounded-lg p-2 pr-8 border border-border/50"
                >
                  {attachment.type.startsWith('image/') ? (
                    <img
                      src={attachment.url}
                      alt={attachment.name}
                      className="h-16 w-16 object-cover rounded"
                    />
                  ) : (
                    <div className="flex items-center gap-2">
                      <Paperclip className="w-4 h-4 text-muted-foreground" />
                      <div>
                        <p className="text-xs font-medium text-foreground truncate max-w-[120px]">
                          {attachment.name}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {formatFileSize(attachment.size)}
                        </p>
                      </div>
                    </div>
                  )}
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => removeAttachment(attachment.id)}
                    className="absolute top-1 right-1 h-5 w-5 rounded-full bg-destructive/20 hover:bg-destructive/40 text-destructive"
                  >
                    <X className="w-3 h-3" />
                  </Button>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

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

        {/* File Attachment Button */}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => fileInputRef.current?.click()}
          className="flex-shrink-0 text-muted-foreground hover:text-fire hover:bg-fire/10"
          title="Attach files"
        >
          <Paperclip className="w-5 h-5" />
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleFileSelect}
          className="hidden"
          accept="image/*,.pdf,.doc,.docx,.txt,.md"
        />

        {/* Voice Mode Button */}
        <Button
          variant="ghost"
          size="icon"
          onClick={onVoiceToggle}
          className={`flex-shrink-0 transition-all duration-300 ${
            voiceMode
              ? isVoiceActive
                ? 'bg-fire/30 text-fire hover:bg-fire/40 animate-pulse'
                : 'bg-fire/20 text-fire hover:bg-fire/30'
              : 'text-muted-foreground hover:text-fire hover:bg-fire/10'
          }`}
          title={voiceMode ? 'Exit Voice Mode' : 'Enter Voice Mode'}
        >
          {voiceMode ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
        </Button>

        {/* Input Area */}
        <div className="flex-1 relative">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={voiceMode ? "Voice mode active - speak or type..." : "Speak to Roboto..."}
            disabled={disabled}
            className="min-h-[48px] max-h-[150px] resize-none pr-12 bg-muted/50 border-border/50 focus:border-primary/50 focus:ring-1 focus:ring-primary/30 placeholder:text-muted-foreground/50 text-foreground"
            rows={1}
          />
        </div>

        {/* Send Button */}
        <Button
          onClick={handleSubmit}
          disabled={(!input.trim() && attachments.length === 0) || disabled}
          className="flex-shrink-0 btn-ember h-12 w-12 p-0 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Send className="w-5 h-5" />
        </Button>
      </div>
    </motion.div>
  );
};
