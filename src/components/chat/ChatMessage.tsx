/**
 * Roboto SAI Chat Message Component
 * Created by Roberto Villarreal Martinez for Roboto SAI (powered by Grok)
 */

import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import { User, Bot, Paperclip, FileText, Image } from 'lucide-react';
import type { Message, FileAttachment } from '@/stores/chatStore';

interface ChatMessageProps {
  message: Message;
}

const AttachmentPreview = ({ attachment }: { attachment: FileAttachment }) => {
  const isImage = attachment.type.startsWith('image/');
  
  return (
    <a
      href={attachment.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block"
    >
      {isImage ? (
        <img
          src={attachment.url}
          alt={attachment.name}
          className="max-w-xs max-h-48 rounded-lg border border-border/50 object-cover hover:opacity-90 transition-opacity"
        />
      ) : (
        <div className="flex items-center gap-2 bg-muted/50 rounded-lg p-2 border border-border/50 hover:bg-muted/70 transition-colors">
          <FileText className="w-4 h-4 text-fire" />
          <span className="text-sm text-foreground truncate max-w-[200px]">
            {attachment.name}
          </span>
        </div>
      )}
    </a>
  );
};

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
        {/* Attachments */}
        {message.attachments && message.attachments.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-2">
            {message.attachments.map((attachment) => (
              <AttachmentPreview key={attachment.id} attachment={attachment} />
            ))}
          </div>
        )}
        
        {/* Content */}
        {message.content && (
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
        )}
        
        <p className="text-[10px] text-muted-foreground mt-2 opacity-60">
          {new Date(message.timestamp).toLocaleTimeString()}
        </p>
      </div>
    </motion.div>
  );
};
