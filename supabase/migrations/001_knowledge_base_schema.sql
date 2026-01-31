-- Roboto SAI Knowledge Base Schema
-- Created by Roberto Villarreal Martinez
-- Production-ready memory system for AI companion that never forgets

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- User memories table - stores all user-specific memories
CREATE TABLE IF NOT EXISTS user_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    importance FLOAT DEFAULT 1.0,
    immutable BOOLEAN DEFAULT FALSE,
    embedding VECTOR(1536), -- For semantic search with OpenAI embeddings
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    accessed_at TIMESTAMPTZ DEFAULT NOW(),
    access_count INTEGER DEFAULT 0
);

-- Create index for fast user lookups
CREATE INDEX IF NOT EXISTS idx_user_memories_user_id ON user_memories(user_id);
CREATE INDEX IF NOT EXISTS idx_user_memories_category ON user_memories(category);
CREATE INDEX IF NOT EXISTS idx_user_memories_importance ON user_memories(importance DESC);
CREATE INDEX IF NOT EXISTS idx_user_memories_created_at ON user_memories(created_at DESC);

-- Conversation summaries - extracted key points from conversations
CREATE TABLE IF NOT EXISTS conversation_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    session_id TEXT NOT NULL,
    summary TEXT NOT NULL,
    key_topics TEXT[] DEFAULT '{}',
    sentiment TEXT,
    importance FLOAT DEFAULT 1.0,
    embedding VECTOR(1536),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conv_summaries_user_id ON conversation_summaries(user_id);
CREATE INDEX IF NOT EXISTS idx_conv_summaries_session ON conversation_summaries(session_id);

-- User preferences - learned preferences and patterns
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    preference_key TEXT NOT NULL,
    preference_value JSONB NOT NULL,
    confidence FLOAT DEFAULT 1.0,
    learned_from TEXT[], -- Session IDs where this was learned
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, preference_key)
);

CREATE INDEX IF NOT EXISTS idx_user_prefs_user_id ON user_preferences(user_id);

-- Entity mentions - people, places, things the user talks about
CREATE TABLE IF NOT EXISTS entity_mentions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    entity_name TEXT NOT NULL,
    entity_type TEXT NOT NULL, -- person, place, thing, concept, etc.
    mention_count INTEGER DEFAULT 1,
    last_context TEXT,
    sentiment_avg FLOAT DEFAULT 0.0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, entity_name, entity_type)
);

CREATE INDEX IF NOT EXISTS idx_entity_mentions_user_id ON entity_mentions(user_id);
CREATE INDEX IF NOT EXISTS idx_entity_mentions_type ON entity_mentions(entity_type);

-- Row Level Security Policies
ALTER TABLE user_memories ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE entity_mentions ENABLE ROW LEVEL SECURITY;

-- Users can only access their own memories
CREATE POLICY "Users can view own memories" ON user_memories
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own memories" ON user_memories
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own memories" ON user_memories
    FOR UPDATE USING (auth.uid() = user_id AND immutable = FALSE);

CREATE POLICY "Users can delete own memories" ON user_memories
    FOR DELETE USING (auth.uid() = user_id AND immutable = FALSE);

-- Similar policies for other tables
CREATE POLICY "Users can access own summaries" ON conversation_summaries
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can access own preferences" ON user_preferences
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can access own entities" ON entity_mentions
    FOR ALL USING (auth.uid() = user_id);

-- Function to update accessed_at and access_count on memory retrieval
CREATE OR REPLACE FUNCTION update_memory_access()
RETURNS TRIGGER AS $$
BEGIN
    NEW.accessed_at = NOW();
    NEW.access_count = OLD.access_count + 1;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for auto-updating timestamps
CREATE TRIGGER trigger_update_memory_timestamp
    BEFORE UPDATE ON user_memories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_update_prefs_timestamp
    BEFORE UPDATE ON user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_update_entities_timestamp
    BEFORE UPDATE ON entity_mentions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();
