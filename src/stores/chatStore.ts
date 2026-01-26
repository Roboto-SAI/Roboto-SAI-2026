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
  addMessage: (message: Omit<Message, 'timestamp'>) => string;
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

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null;

const reviveDate = (value: unknown): Date => {
  const date = value instanceof Date
    ? value
    : (typeof value === 'string' || typeof value === 'number')
      ? new Date(value)
      : new Date();

  return Number.isNaN(date.valueOf()) ? new Date() : date;
};

const reviveMessage = (value: unknown): Message => {
  if (!isRecord(value)) {
    return {
      id: crypto.randomUUID(),
      role: 'user',
      content: '',
      timestamp: new Date(),
    };
  }

  return {
    id: typeof value.id === 'string' ? value.id : crypto.randomUUID(),
    role: value.role === 'assistant' ? 'assistant' : 'user',
    content: typeof value.content === 'string' ? value.content : '',
    timestamp: reviveDate(value.timestamp),
    attachments: Array.isArray(value.attachments) ? (value.attachments as FileAttachment[]) : undefined,
    emotion: typeof value.emotion === 'string' ? value.emotion : undefined,
    emotion_text: typeof value.emotion_text === 'string' ? value.emotion_text : undefined,
    emotion_probabilities: isRecord(value.emotion_probabilities)
      ? (value.emotion_probabilities as Record<string, number>)
      : undefined,
    session_id: typeof value.session_id === 'string' ? value.session_id : undefined,
    created_at: typeof value.created_at === 'string' ? value.created_at : undefined,
    user_id: typeof value.user_id === 'string' ? value.user_id : undefined,
  };
};

const reviveConversation = (value: unknown): Conversation | null => {
  if (!isRecord(value)) return null;

  const messages = Array.isArray(value.messages)
    ? (value.messages as unknown[]).map(reviveMessage)
    : [];

  return {
    id: typeof value.id === 'string' ? value.id : crypto.randomUUID(),
    title: typeof value.title === 'string' ? value.title : 'New Chat',
    messages,
    createdAt: reviveDate(value.createdAt),
    updatedAt: reviveDate(value.updatedAt),
  };
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
        const allMessages = (state.conversations ?? [])
          .flatMap(conv => Array.isArray(conv.messages) ? conv.messages : [])
          .sort((a, b) => {
            const timeA = a.timestamp instanceof Date
              ? a.timestamp.getTime()
              : new Date(a.timestamp ?? 0).getTime();
            const timeB = b.timestamp instanceof Date
              ? b.timestamp.getTime()
              : new Date(b.timestamp ?? 0).getTime();
            return timeA - timeB;
          });

        const maxMessages = 50; // Increased for more history
        const recent = allMessages.slice(-maxMessages);
        const filtered = recent.filter(message => {
          if (message.role !== 'assistant') return true;
          const content = typeof message.content === 'string' ? message.content : '';
          return !content.startsWith('⚠️ **Connection to the flame matrix interrupted.**');
        });
        let context = filtered
          .map(message => {
            const safeContent = typeof message.content === 'string' ? message.content : '';
            return `${message.role}: ${safeContent.substring(0, 500)}`; // Increased truncation per message
          })
          .join('\n');
        return context.length > 100000 ? context.substring(0, 100000) + '\n... (truncated)' : context; // Increased total cap to 100k chars
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
        let createdConversationId: string | null = null;

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
            id: typeof message.id === 'string' 
              ? message.id 
              : crypto.randomUUID(),
            timestamp: new Date(),
            session_id: conversationId,
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
          
          createdConversationId = conversationId;

          return {
            conversations,
            currentConversationId: conversationId,
          };
        });

        return createdConversationId ?? crypto.randomUUID();
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
          const fallbackBase = globalThis.window?.location.origin ?? '';
          const apiBaseUrl = (envUrl || fallbackBase).replace(/\/+$/, '').replace(/\/api$/, '');
          const url = `${apiBaseUrl}/api/chat/history?limit=200`;
          const res = await fetch(url, { credentials: 'include' });
          if (!res.ok) throw new Error('Failed to load history');
          const data = await res.json();
          const messages = data.messages || [];
          
          // Group by session_id
          const groups = new Map<string, Conversation>();
          messages.forEach((msg: Message & { created_at?: string }) => {
            const sessId = msg.session_id || 'default';
            let conv = groups.get(sessId);
            if (!conv) {
              conv = {
                id: sessId,
                title: 'Chat',
                messages: [],
                createdAt: new Date(),
                updatedAt: new Date(),
              };
              groups.set(sessId, conv);
            }
            const createdAt = msg.created_at ? new Date(msg.created_at) : new Date();
            const probabilities = typeof msg.emotion_probabilities === 'string'
              ? (() => {
                  try {
                    return JSON.parse(msg.emotion_probabilities as string);
                  } catch {
                    return undefined;
                  }
                })()
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
        const envelope = isRecord(persistedState) ? persistedState : null;
        const rawState = envelope && 'state' in envelope ? envelope.state : persistedState;

        const userId = isRecord(rawState) && typeof rawState.userId === 'string' ? rawState.userId : null;
        const currentTheme = isRecord(rawState) && typeof rawState.currentTheme === 'string'
          ? rawState.currentTheme
          : 'Regio-Aztec Fire #42';

        if (!isRecord(rawState) || !userId) {
          return {
            conversations: [],
            currentConversationId: null,
            currentTheme,
            userId: null,
          } as Partial<ChatState>;
        }

        const revivedConversations = Array.isArray(rawState.conversations)
          ? (rawState.conversations as unknown[])
              .map(reviveConversation)
              .filter((c): c is Conversation => c !== null)
          : [];

        const validCurrentId = revivedConversations.find(c => c.id === rawState.currentConversationId)?.id || null;

        return {
          conversations: revivedConversations,
          currentConversationId: validCurrentId,
          currentTheme,
          userId,
        } as Partial<ChatState>;
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

