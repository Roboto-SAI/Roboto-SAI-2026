BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE conversation_summaries
    ADD COLUMN IF NOT EXISTS entities JSONB DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS sentiment_score FLOAT CHECK (sentiment_score >= -1 AND sentiment_score <= 1),
    ADD COLUMN IF NOT EXISTS message_count INTEGER DEFAULT 0 CHECK (message_count >= 0),
    ADD COLUMN IF NOT EXISTS duration_minutes INTEGER CHECK (duration_minutes IS NULL OR duration_minutes >= 0),
    ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS conversation_start TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS conversation_end TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_conv_summaries_created_at ON conversation_summaries(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conv_summaries_importance ON conversation_summaries(importance DESC);
CREATE INDEX IF NOT EXISTS idx_conv_summaries_sentiment ON conversation_summaries(sentiment);
CREATE INDEX IF NOT EXISTS idx_conv_summaries_user_session ON conversation_summaries(user_id, session_id);
CREATE INDEX IF NOT EXISTS idx_conv_summaries_entities ON conversation_summaries USING GIN (entities);
CREATE INDEX IF NOT EXISTS idx_conv_summaries_summary_fts ON conversation_summaries USING GIN (to_tsvector('english', summary));

CREATE INDEX IF NOT EXISTS idx_conv_summaries_embedding ON conversation_summaries
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

ALTER TABLE conversation_summaries ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can access own summaries" ON conversation_summaries;

CREATE POLICY "Users can view own summaries" ON conversation_summaries
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own summaries" ON conversation_summaries
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own summaries" ON conversation_summaries
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own summaries" ON conversation_summaries
    FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage summaries" ON conversation_summaries
    FOR ALL USING (auth.role() = 'service_role');

DROP TRIGGER IF EXISTS trigger_update_conversation_summaries_timestamp ON conversation_summaries;
CREATE TRIGGER trigger_update_conversation_summaries_timestamp
    BEFORE UPDATE ON conversation_summaries
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE OR REPLACE FUNCTION search_conversation_summaries(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10,
    target_user_id UUID DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    session_id TEXT,
    summary TEXT,
    key_topics TEXT[],
    sentiment TEXT,
    importance FLOAT,
    similarity FLOAT,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        cs.id,
        cs.session_id,
        cs.summary,
        cs.key_topics,
        cs.sentiment,
        cs.importance,
        1 - (cs.embedding <=> query_embedding) as similarity,
        cs.created_at
    FROM conversation_summaries cs
    WHERE
        (target_user_id IS NULL OR cs.user_id = target_user_id)
        AND 1 - (cs.embedding <=> query_embedding) > match_threshold
    ORDER BY cs.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT SELECT, INSERT, UPDATE, DELETE ON conversation_summaries TO authenticated;
GRANT EXECUTE ON FUNCTION search_conversation_summaries TO authenticated;

COMMIT;
