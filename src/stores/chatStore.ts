/**
 * Roboto SAI Chat Store
 * Created by Roberto Villarreal Martinez for Roboto SAI (powered by Grok)
 * Integrated with FastAPI backend
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface FileAttachment {
  id: string;
  name: string;
  type: string;
  size: number;
  url: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  attachments?: FileAttachment[];
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
}

interface ChatState {
  conversations: Conversation[];
  currentConversationId: string | null;
  isLoading: boolean;
  ventMode: boolean;
  currentTheme: string;
  voiceMode: boolean;
  
  // Getters
  getCurrentConversation: () => Conversation | undefined;
  getMessages: () => Message[];
  getAllConversationsContext: () => string;
  
  // Actions
  createNewConversation: () => string;
  selectConversation: (id: string) => void;
  deleteConversation: (id: string) => void;
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  setLoading: (loading: boolean) => void;
  toggleVentMode: () => void;
  setTheme: (theme: string) => void;
  clearMessages: () => void;
  toggleVoiceMode: () => void;
    }),
    {
      name: 'roboto-sai-chat-storage',
      partialize: (state) => ({
        conversations: state.conversations,
        currentConversationId: state.currentConversationId,
        currentTheme: state.currentTheme,
      }),
    }
  )
);

const generateTitle = (content: string): string => {
  const cleaned = content.replace(/[^\w\s]/g, '').trim();
  const words = cleaned.split(/\s+/).slice(0, 5);
  return words.join(' ') || 'New Chat';
};

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      conversations: [],
      currentConversationId: null,
      isLoading: false,
      ventMode: false,
      currentTheme: 'Regio-Aztec Fire #42',
      voiceMode: false,
      
      getCurrentConversation: () => {
        const state = get();
        return state.conversations.find(c => c.id === state.currentConversationId);
      },
      
      getMessages: () => {
        const conversation = get().getCurrentConversation();
        return conversation?.messages || [];
      },
      
      getAllConversationsContext: () => {
        const state = get();
        return state.conversations
          .map(conv => {
            const summary = conv.messages.slice(0, 3).map(m => 
              `${m.role}: ${m.content.slice(0, 100)}...`
            ).join('\n');
            return `[${conv.title}]\n${summary}`;
          })
          .join('\n\n---\n\n');
      },
      
      createNewConversation: () => {
        const newId = crypto.randomUUID();
        const newConversation: Conversation = {
          id: newId,
          title: 'New Chat',
          messages: [],
          createdAt: new Date(),
          updatedAt: new Date(),
        };
        
        set((state) => ({
          conversations: [newConversation, ...state.conversations],
          currentConversationId: newId,
        }));
        
        return newId;
      },
      
      selectConversation: (id) => {
        set({ currentConversationId: id });
      },
      
      deleteConversation: (id) => {
        set((state) => {
          const filtered = state.conversations.filter(c => c.id !== id);
          const newCurrentId = state.currentConversationId === id 
            ? (filtered[0]?.id || null)
            : state.currentConversationId;
          return {
            conversations: filtered,
            currentConversationId: newCurrentId,
          };
        });
      },
      
      addMessage: (message) => {
        set((state) => {
          let conversationId = state.currentConversationId;
          let conversations = [...state.conversations];
          
          // Create new conversation if none exists
          if (!conversationId) {
            conversationId = crypto.randomUUID();
            const newConversation: Conversation = {
              id: conversationId,
              title: message.role === 'user' ? generateTitle(message.content) : 'New Chat',
              messages: [],
              createdAt: new Date(),
              updatedAt: new Date(),
            };
            conversations = [newConversation, ...conversations];
          }
          
          const newMessage: Message = {
            ...message,
            id: crypto.randomUUID(),
            timestamp: new Date(),
          };
          
          conversations = conversations.map(conv => {
            if (conv.id === conversationId) {
              const updatedMessages = [...conv.messages, newMessage];
              // Update title if first user message
              const shouldUpdateTitle = conv.title === 'New Chat' && 
                message.role === 'user' && 
                conv.messages.length === 0;
              
              return {
                ...conv,
                messages: updatedMessages,
                title: shouldUpdateTitle ? generateTitle(message.content) : conv.title,
                updatedAt: new Date(),
              };
            }
            return conv;
          });
          
          return {
            conversations,
            currentConversationId: conversationId,
          };
        });
      },
      
      setLoading: (loading) => set({ isLoading: loading }),
      
      toggleVentMode: () => set((state) => ({ ventMode: !state.ventMode })),
      
      setTheme: (theme) => set({ currentTheme: theme }),
      
      clearMessages: () => {
        set((state) => {
          if (!state.currentConversationId) return state;
          
          return {
            conversations: state.conversations.map(conv => 
              conv.id === state.currentConversationId 
                ? { ...conv, messages: [], updatedAt: new Date() }
                : conv
            ),
          };
        });
      },
      
      toggleVoiceMode: () => set((state) => ({ voiceMode: !state.voiceMode })),
    }),
    {
      name: 'roboto-sai-chat-storage',
      partialize: (state) => ({
        conversations: state.conversations,
        currentConversationId: state.currentConversationId,
        currentTheme: state.currentTheme,
      }),
    }
  )
);

