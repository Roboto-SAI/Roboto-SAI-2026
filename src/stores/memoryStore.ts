/**
 * Roboto SAI Memory Store
 * Production-ready Supabase-backed memory system
 * Created by Roberto Villarreal Martinez for Roboto SAI
 * 
 * This store manages user memories that persist across sessions,
 * enabling Roboto to never forget important information about each user.
 */

import { create } from 'zustand';
import { createClient, SupabaseClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

let supabase: SupabaseClient | null = null;
if (supabaseUrl && supabaseKey) {
  supabase = createClient(supabaseUrl, supabaseKey);
}

export interface Memory {
  id: string;
  user_id: string;
  content: string;
  category: string;
  importance: number;
  immutable: boolean;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  accessed_at: string;
  access_count: number;
}

export interface ConversationSummary {
  id: string;
  user_id: string;
  session_id: string;
  summary: string;
  key_topics: string[];
  sentiment: string | null;
  importance: number;
  created_at: string;
}

export interface UserPreference {
  id: string;
  user_id: string;
  preference_key: string;
  preference_value: unknown;
  confidence: number;
  learned_from: string[];
  created_at: string;
  updated_at: string;
}

export interface EntityMention {
  id: string;
  user_id: string;
  entity_name: string;
  entity_type: string;
  mention_count: number;
  last_context: string | null;
  sentiment_avg: number;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

interface MemoryState {
  memories: Memory[];
  summaries: ConversationSummary[];
  preferences: UserPreference[];
  entities: EntityMention[];
  isLoading: boolean;
  isReady: boolean;
  error: string | null;
  currentUserId: string | null;

  // Core operations
  loadUserMemories: (userId: string) => Promise<void>;
  addMemory: (content: string, category?: string, importance?: number, metadata?: Record<string, unknown>) => Promise<string | null>;
  updateMemory: (id: string, updates: Partial<Pick<Memory, 'content' | 'category' | 'importance' | 'metadata'>>) => Promise<boolean>;
  deleteMemory: (id: string) => Promise<boolean>;
  
  // Query operations
  searchMemories: (query: string, limit?: number) => Promise<Memory[]>;
  getMemoriesByCategory: (category: string) => Memory[];
  getImportantMemories: (minImportance?: number) => Memory[];
  
  // Conversation summary operations
  addConversationSummary: (sessionId: string, summary: string, keyTopics?: string[], sentiment?: string) => Promise<string | null>;
  
  // Preference operations
  setPreference: (key: string, value: unknown, confidence?: number, sessionId?: string) => Promise<boolean>;
  getPreference: (key: string) => unknown | null;
  
  // Entity operations
  trackEntity: (name: string, type: string, context?: string, sentiment?: number) => Promise<boolean>;
  getEntitiesByType: (type: string) => EntityMention[];
  
  // Context building for AI
  buildContextForAI: (query?: string, maxTokens?: number) => string;
  
  // Utility
  reset: () => void;
}

// Permanent core memories about Roberto (immutable, always included)
const CORE_MEMORIES = [
  {
    content: 'Roberto Villarreal Martinez is the sole creator and owner of Roboto SAI. Sigil 929 marks eternal ownership. Born September 21, 1999, Houston TX.',
    category: 'identity',
    importance: 2.0,
    immutable: true,
  },
  {
    content: 'Roboto SAI is an AI companion that never forgets. Every conversation matters. Every memory persists. The eternal flame of knowledge burns forever.',
    category: 'identity',
    importance: 2.0,
    immutable: true,
  },
];

export const useMemoryStore = create<MemoryState>()((set, get) => ({
  memories: [],
  summaries: [],
  preferences: [],
  entities: [],
  isLoading: false,
  isReady: false,
  error: null,
  currentUserId: null,

  loadUserMemories: async (userId: string) => {
    if (!supabase) {
      set({ error: 'Memory service not configured', isReady: false });
      return;
    }

    set({ isLoading: true, error: null, currentUserId: userId });

    try {
      // Load memories
      const { data: memories, error: memError } = await supabase
        .from('user_memories')
        .select('*')
        .eq('user_id', userId)
        .order('importance', { ascending: false })
        .order('accessed_at', { ascending: false });

      if (memError) throw memError;

      // Load conversation summaries (optional - table may not exist yet)
      let summaries = [];
      try {
        const { data: summaryData, error: sumError } = await supabase
          .from('conversation_summaries')
          .select('*')
          .eq('user_id', userId)
          .order('created_at', { ascending: false })
          .limit(50);

        if (!sumError && summaryData) {
          summaries = summaryData;
        }
      } catch (err) {
        console.warn('conversation_summaries table not available:', err);
      }

      // Load preferences
      const { data: preferences, error: prefError } = await supabase
        .from('user_preferences')
        .select('*')
        .eq('user_id', userId);

      if (prefError) throw prefError;

      // Load entities
      const { data: entities, error: entError } = await supabase
        .from('entity_mentions')
        .select('*')
        .eq('user_id', userId)
        .order('mention_count', { ascending: false })
        .limit(100);

      if (entError) throw entError;

      set({
        memories: memories || [],
        summaries: summaries || [],
        preferences: preferences || [],
        entities: entities || [],
        isLoading: false,
        isReady: true,
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to load memories',
        isLoading: false,
        isReady: false,
      });
    }
  },

  addMemory: async (content, category = 'general', importance = 1.0, metadata = {}) => {
    const { currentUserId } = get();
    if (!supabase || !currentUserId) return null;

    try {
      const { data, error } = await supabase
        .from('user_memories')
        .insert({
          user_id: currentUserId,
          content,
          category,
          importance,
          metadata,
          immutable: false,
        })
        .select()
        .single();

      if (error) throw error;

      set((state) => ({
        memories: [data, ...state.memories],
      }));

      return data.id;
    } catch (error) {
      console.error('Failed to add memory:', error);
      return null;
    }
  },

  updateMemory: async (id, updates) => {
    if (!supabase) return false;

    try {
      const { error } = await supabase
        .from('user_memories')
        .update(updates)
        .eq('id', id)
        .eq('immutable', false);

      if (error) throw error;

      set((state) => ({
        memories: state.memories.map((m) =>
          m.id === id ? { ...m, ...updates } : m
        ),
      }));

      return true;
    } catch (error) {
      console.error('Failed to update memory:', error);
      return false;
    }
  },

  deleteMemory: async (id) => {
    if (!supabase) return false;

    try {
      const { error } = await supabase
        .from('user_memories')
        .delete()
        .eq('id', id)
        .eq('immutable', false);

      if (error) throw error;

      set((state) => ({
        memories: state.memories.filter((m) => m.id !== id),
      }));

      return true;
    } catch (error) {
      console.error('Failed to delete memory:', error);
      return false;
    }
  },

  searchMemories: async (query, limit = 10) => {
    const { memories } = get();
    
    // Simple keyword search (can be enhanced with embeddings later)
    const lowerQuery = query.toLowerCase();
    const results = memories
      .filter((m) => m.content.toLowerCase().includes(lowerQuery))
      .slice(0, limit);

    return results;
  },

  getMemoriesByCategory: (category) => {
    return get().memories.filter((m) => m.category === category);
  },

  getImportantMemories: (minImportance = 1.5) => {
    return get().memories.filter((m) => m.importance >= minImportance);
  },

  addConversationSummary: async (sessionId, summary, keyTopics = [], sentiment) => {
    const { currentUserId } = get();
    if (!supabase || !currentUserId) return null;

    try {
      const { data, error } = await supabase
        .from('conversation_summaries')
        .insert({
          user_id: currentUserId,
          session_id: sessionId,
          summary,
          key_topics: keyTopics,
          sentiment,
          importance: 1.0,
        })
        .select()
        .single();

      // Handle missing table gracefully (PostgreSQL error code 42P01)
      if (error?.code === '42P01') {
        console.info('conversation_summaries table not yet created, skipping summary storage');
        return null;
      }
      
      if (error) throw error;

      set((state) => ({
        summaries: [data, ...state.summaries.slice(0, 49)],
      }));

      return data.id;
    } catch (error) {
      console.error('Failed to add conversation summary:', error);
      return null;
    }
  },

  setPreference: async (key, value, confidence = 1.0, sessionId) => {
    const { currentUserId, preferences } = get();
    if (!supabase || !currentUserId) return false;

    const existing = preferences.find((p) => p.preference_key === key);

    try {
      if (existing) {
        const learnedFrom = sessionId
          ? [...new Set([...(existing.learned_from || []), sessionId])]
          : existing.learned_from;

        const { error } = await supabase
          .from('user_preferences')
          .update({
            preference_value: value,
            confidence,
            learned_from: learnedFrom,
          })
          .eq('id', existing.id);

        if (error) throw error;

        set((state) => ({
          preferences: state.preferences.map((p) =>
            p.id === existing.id
              ? { ...p, preference_value: value, confidence, learned_from: learnedFrom }
              : p
          ),
        }));
      } else {
        const { data, error } = await supabase
          .from('user_preferences')
          .insert({
            user_id: currentUserId,
            preference_key: key,
            preference_value: value,
            confidence,
            learned_from: sessionId ? [sessionId] : [],
          })
          .select()
          .single();

        if (error) throw error;

        set((state) => ({
          preferences: [...state.preferences, data],
        }));
      }

      return true;
    } catch (error) {
      console.error('Failed to set preference:', error);
      return false;
    }
  },

  getPreference: (key) => {
    const pref = get().preferences.find((p) => p.preference_key === key);
    return pref?.preference_value ?? null;
  },

  trackEntity: async (name, type, context, sentiment) => {
    const { currentUserId, entities } = get();
    if (!supabase || !currentUserId) return false;

    const existing = entities.find(
      (e) => e.entity_name === name && e.entity_type === type
    );

    try {
      if (existing) {
        const newCount = existing.mention_count + 1;
        const newSentiment = sentiment !== undefined
          ? (existing.sentiment_avg * existing.mention_count + sentiment) / newCount
          : existing.sentiment_avg;

        const { error } = await supabase
          .from('entity_mentions')
          .update({
            mention_count: newCount,
            last_context: context || existing.last_context,
            sentiment_avg: newSentiment,
          })
          .eq('id', existing.id);

        if (error) throw error;

        set((state) => ({
          entities: state.entities.map((e) =>
            e.id === existing.id
              ? { ...e, mention_count: newCount, last_context: context || e.last_context, sentiment_avg: newSentiment }
              : e
          ),
        }));
      } else {
        const { data, error } = await supabase
          .from('entity_mentions')
          .insert({
            user_id: currentUserId,
            entity_name: name,
            entity_type: type,
            mention_count: 1,
            last_context: context,
            sentiment_avg: sentiment || 0,
          })
          .select()
          .single();

        if (error) throw error;

        set((state) => ({
          entities: [...state.entities, data],
        }));
      }

      return true;
    } catch (error) {
      console.error('Failed to track entity:', error);
      return false;
    }
  },

  getEntitiesByType: (type) => {
    return get().entities.filter((e) => e.entity_type === type);
  },

  buildContextForAI: (query, maxTokens = 4000) => {
    const { memories, summaries, preferences, entities } = get();
    const parts: string[] = [];

    // Add core memories first
    parts.push('## Core Knowledge');
    CORE_MEMORIES.forEach((m) => parts.push(`- ${m.content}`));

    // Add important user memories
    const importantMemories = memories.filter((m) => m.importance >= 1.5).slice(0, 10);
    if (importantMemories.length > 0) {
      parts.push('\n## Important User Memories');
      importantMemories.forEach((m) => parts.push(`- [${m.category}] ${m.content}`));
    }

    // Add relevant memories based on query
    if (query) {
      const lowerQuery = query.toLowerCase();
      const relevantMemories = memories
        .filter((m) => m.content.toLowerCase().includes(lowerQuery) && m.importance < 1.5)
        .slice(0, 5);
      if (relevantMemories.length > 0) {
        parts.push('\n## Relevant Memories');
        relevantMemories.forEach((m) => parts.push(`- ${m.content}`));
      }
    }

    // Add recent conversation summaries
    const recentSummaries = summaries.slice(0, 5);
    if (recentSummaries.length > 0) {
      parts.push('\n## Recent Conversation Summaries');
      recentSummaries.forEach((s) => parts.push(`- ${s.summary}`));
    }

    // Add key preferences
    if (preferences.length > 0) {
      parts.push('\n## User Preferences');
      preferences.slice(0, 10).forEach((p) => {
        parts.push(`- ${p.preference_key}: ${JSON.stringify(p.preference_value)}`);
      });
    }

    // Add frequently mentioned entities
    const topEntities = entities.slice(0, 10);
    if (topEntities.length > 0) {
      parts.push('\n## Known Entities');
      topEntities.forEach((e) => {
        parts.push(`- ${e.entity_name} (${e.entity_type}): mentioned ${e.mention_count}x`);
      });
    }

    let context = parts.join('\n');
    
    // Truncate if too long (rough token estimate: 4 chars = 1 token)
    const maxChars = maxTokens * 4;
    if (context.length > maxChars) {
      context = context.substring(0, maxChars) + '\n... (truncated)';
    }

    return context;
  },

  reset: () => {
    set({
      memories: [],
      summaries: [],
      preferences: [],
      entities: [],
      isLoading: false,
      isReady: false,
      error: null,
      currentUserId: null,
    });
  },
}));
