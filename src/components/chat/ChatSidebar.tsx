/**
 * Roboto SAI Chat Sidebar
 * Created by Roberto Villarreal Martinez for Roboto SAI (powered by Grok)
 */

import { motion, AnimatePresence } from 'framer-motion';
import { Plus, MessageSquare, Trash2, X, ChevronLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useChatStore } from '@/stores/chatStore';

interface ChatSidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ChatSidebar = ({ isOpen, onClose }: ChatSidebarProps) => {
  const { 
    conversations, 
    currentConversationId, 
    createNewConversation, 
    selectConversation,
    deleteConversation 
  } = useChatStore();

  const handleNewChat = () => {
    createNewConversation();
  };

  const handleSelectConversation = (id: string) => {
    selectConversation(id);
    onClose();
  };

  const handleDeleteConversation = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    deleteConversation(id);
  };

  return (
    <>
      {/* Overlay */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40 lg:hidden"
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <motion.aside
        initial={{ x: -320 }}
        animate={{ x: isOpen ? 0 : -320 }}
        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
        className="fixed left-0 top-0 bottom-0 w-80 bg-card border-r border-border/50 z-50 flex flex-col"
      >
        {/* Header */}
        <div className="p-4 border-b border-border/50 flex items-center justify-between">
          <h2 className="font-display text-lg text-fire">Chat History</h2>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground"
          >
            <ChevronLeft className="w-5 h-5" />
          </Button>
        </div>

        {/* New Chat Button */}
        <div className="p-4">
          <Button
            onClick={handleNewChat}
            className="w-full btn-ember gap-2"
          >
            <Plus className="w-4 h-4" />
            New Chat
          </Button>
        </div>

        {/* Conversations List */}
        <ScrollArea className="flex-1 px-4">
          <div className="space-y-2 pb-4">
            <AnimatePresence mode="popLayout">
              {conversations.length === 0 ? (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-muted-foreground text-sm text-center py-8"
                >
                  No conversations yet. Start a new chat!
                </motion.p>
              ) : (
                conversations.map((conversation) => (
                  <motion.div
                    key={conversation.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    onClick={() => handleSelectConversation(conversation.id)}
                    className={`group relative p-3 rounded-lg cursor-pointer transition-all ${
                      conversation.id === currentConversationId
                        ? 'bg-fire/20 border border-fire/30'
                        : 'bg-muted/30 hover:bg-muted/50 border border-transparent'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <MessageSquare className={`w-4 h-4 mt-0.5 flex-shrink-0 ${
                        conversation.id === currentConversationId 
                          ? 'text-fire' 
                          : 'text-muted-foreground'
                      }`} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-foreground truncate">
                          {conversation.title}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {conversation.messages.length} messages
                        </p>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={(e) => handleDeleteConversation(e, conversation.id)}
                        className="opacity-0 group-hover:opacity-100 h-6 w-6 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                      >
                        <Trash2 className="w-3 h-3" />
                      </Button>
                    </div>
                  </motion.div>
                ))
              )}
            </AnimatePresence>
          </div>
        </ScrollArea>

        {/* Footer */}
        <div className="p-4 border-t border-border/50">
          <p className="text-xs text-muted-foreground text-center">
            All chats are stored locally
          </p>
        </div>
      </motion.aside>
    </>
  );
};
