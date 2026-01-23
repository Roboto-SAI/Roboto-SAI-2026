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
  emotion?: string;
  emotion_text?: string;
  emotion_probabilities?: Record<string, number>;
  session_id?: string;
  created_at?: string;
  user_id?: string;
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
  userId: string | null;
  
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
  loadUserHistory: (userId: string) => Promise<void>;
  resetConversations: () => void;
}

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
      userId: null,
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
        const allMessages = state.conversations
          .flatMap(conv => conv.messages)
          .sort((a, b) => a.timestamp.getTime() - b.timestamp.getTime());

        const maxMessages = 200;
        const recent = allMessages.slice(-maxMessages);
        return recent
          .map(message => `${message.role}: ${message.content}`)
          .join('\n');
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
      loadUserHistory: async (userId: string) => {
        try {
          set({ conversations: [], currentConversationId: null, userId });
          const envUrl = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || '';
          const apiBaseUrl = envUrl.replace(/\/+$/, '').replace(/\/api$/, '');
          const url = `${apiBaseUrl}/api/chat/history?limit=200`;
          const res = await fetch(url, { credentials: 'include' });
          if (!res.ok) throw new Error('Failed to load history');
          const data = await res.json();
          const messages = data.messages || [];
          
          // Group by session_id
          const groups = new Map<string, Conversation>();
          messages.forEach((msg: Message & { created_at?: string }) => {
            const sessId = msg.session_id || 'default';
            if (!groups.has(sessId)) {
              groups.set(sessId, {
                id: sessId,
                title: 'Chat',
                messages: [],
                createdAt: new Date(),
                updatedAt: new Date(),
              });
            }
            const conv = groups.get(sessId)!;
            const createdAt = msg.created_at ? new Date(msg.created_at) : new Date();
            const probabilities = typeof msg.emotion_probabilities === 'string'
              ? JSON.parse(msg.emotion_probabilities)
              : msg.emotion_probabilities;

            const storeMsg: Message = {
              id: String(msg.id),
              role: msg.role,
              content: msg.content,
              timestamp: createdAt,
              emotion: msg.emotion,
              emotion_text: msg.emotion_text,
              emotion_probabilities: probabilities,
              session_id: msg.session_id,
              user_id: msg.user_id,
            };

            conv.messages.push(storeMsg);
            // Update title from first user message
            if (msg.role === 'user' && conv.title === 'Chat' && conv.messages.length === 1) {
              conv.title = generateTitle(msg.content);
            }
            conv.updatedAt = createdAt;
            if (conv.messages.length === 1) {
              conv.createdAt = createdAt;
            }
          });
          
          const convs = Array.from(groups.values()).sort((a, b) => 
            b.updatedAt.getTime() - a.updatedAt.getTime()
          );
          
          set({ 
            conversations: convs,
            userId,
            currentConversationId: convs[0]?.id || null 
          });
        } catch (error) {
          console.error('Load history failed:', error);
        }
      },
      resetConversations: () => {
        set({
          conversations: [],
          currentConversationId: null,
          userId: null,
        });
      },
    }),
    {
      name: 'roboto-sai-chat-storage',
      version: 2,
      migrate: (persistedState: unknown) => {
        const state = persistedState as ChatState;
        if (!state.userId) {
          return state;
        }
        return state;
      },
      partialize: (state) => ({
        conversations: state.conversations,
        currentConversationId: state.currentConversationId,
        currentTheme: state.currentTheme,
        userId: state.userId,
      }),
    }
  )
);

