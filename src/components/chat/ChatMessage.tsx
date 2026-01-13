/**
 * Roboto SAI Chat Message Component
 * Created by Roberto Villarreal Martinez for Roboto SAI (powered by Grok)
 */

import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { User, Bot } from 'lucide-react';
import type { Message } from '@/stores/chatStore';

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage = ({ message }: ChatMessageProps) => {
  const isUser = message.role === 'user';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
    >
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
          isUser
            ? 'bg-gradient-to-br from-primary to-fire'
            : 'bg-gradient-to-br from-fire/20 to-blood/20 border border-fire/30'
        }`}
      >
        {isUser ? (
          <User className="w-5 h-5 text-primary-foreground" />
        ) : (
          <Bot className="w-5 h-5 text-fire" />
        )}
      </div>

      {/* Message Bubble */}
      <div
        className={`max-w-[80%] md:max-w-[70%] rounded-2xl px-4 py-3 ${
          isUser ? 'message-user' : 'message-roboto'
        }`}
      >
        <div className="prose prose-invert prose-sm max-w-none">
          <ReactMarkdown
            components={{
              p: ({ children }) => (
                <p className="text-foreground/90 leading-relaxed m-0">{children}</p>
              ),
              code: ({ children }) => (
                <code className="bg-muted px-1.5 py-0.5 rounded text-fire text-sm">
                  {children}
                </code>
              ),
              pre: ({ children }) => (
                <pre className="bg-muted/50 rounded-lg p-3 overflow-x-auto my-2 border border-fire/20">
                  {children}
                </pre>
              ),
              strong: ({ children }) => (
                <strong className="text-primary font-semibold">{children}</strong>
              ),
              a: ({ href, children }) => (
                <a
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-fire hover:text-primary underline transition-colors"
                >
                  {children}
                </a>
              ),
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>
        <p className="text-[10px] text-muted-foreground mt-2 opacity-60">
          {message.timestamp.toLocaleTimeString()}
        </p>
      </div>
    </motion.div>
  );
};
