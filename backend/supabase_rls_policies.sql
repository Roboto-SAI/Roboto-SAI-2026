-- Row Level Security (RLS) Policies for Roboto SAI Database
-- This migration creates RLS policies for all tables to ensure secure data access

-- Enable RLS on all tables (already enabled via Supabase dashboard)
-- Note: RLS is already enabled on all tables according to mcp_supabase_list_tables

-- ===== USERS TABLE POLICIES =====
-- Users can only read their own profile
CREATE POLICY "Users can view own profile" ON public.users
  FOR SELECT USING (auth.uid() = id);

-- Users can update their own profile
CREATE POLICY "Users can update own profile" ON public.users
  FOR UPDATE USING (auth.uid() = id);

-- Users can insert their own profile (for registration)
CREATE POLICY "Users can insert own profile" ON public.users
  FOR INSERT WITH CHECK (auth.uid() = id);

-- ===== AUTH_SESSIONS TABLE POLICIES =====
-- Users can only manage their own sessions
CREATE POLICY "Users can view own sessions" ON public.auth_sessions
  FOR SELECT USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can insert own sessions" ON public.auth_sessions
  FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

CREATE POLICY "Users can update own sessions" ON public.auth_sessions
  FOR UPDATE USING (auth.uid()::text = user_id::text);

CREATE POLICY "Users can delete own sessions" ON public.auth_sessions
  FOR DELETE USING (auth.uid()::text = user_id::text);

-- ===== MESSAGES TABLE POLICIES =====
-- Users can view messages from their conversations
CREATE POLICY "Users can view own messages" ON public.messages
  FOR SELECT USING (auth.uid() = user_id);

-- Users can insert messages in their conversations
CREATE POLICY "Users can insert own messages" ON public.messages
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can update their own messages
CREATE POLICY "Users can update own messages" ON public.messages
  FOR UPDATE USING (auth.uid() = user_id);

-- ===== MESSAGE_FEEDBACK TABLE POLICIES =====
-- Users can view feedback on their messages
CREATE POLICY "Users can view feedback on own messages" ON public.message_feedback
  FOR SELECT USING (
    auth.uid() = user_id OR
    EXISTS (
      SELECT 1 FROM public.messages
      WHERE messages.id = message_feedback.message_id
      AND messages.user_id = auth.uid()
    )
  );

-- Users can insert feedback on messages they can see
CREATE POLICY "Users can insert feedback on accessible messages" ON public.message_feedback
  FOR INSERT WITH CHECK (
    auth.uid() = user_id AND
    EXISTS (
      SELECT 1 FROM public.messages
      WHERE messages.id = message_feedback.message_id
    )
  );

-- Users can update their own feedback
CREATE POLICY "Users can update own feedback" ON public.message_feedback
  FOR UPDATE USING (auth.uid() = user_id);

-- Users can delete their own feedback
CREATE POLICY "Users can delete own feedback" ON public.message_feedback
  FOR DELETE USING (auth.uid() = user_id);

-- ===== MAGIC_LINK_TOKENS TABLE POLICIES =====
-- Magic link tokens should be accessible only by the system
-- Users don't need direct access to magic link tokens
-- (This table is used internally by Supabase Auth)

-- Service role can manage all magic link tokens
CREATE POLICY "Service role can manage magic link tokens" ON public.magic_link_tokens
  FOR ALL USING (auth.role() = 'service_role');

-- ===== ADDITIONAL SECURITY MEASURES =====

-- Ensure all tables have RLS enabled (double-check)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.auth_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.message_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.magic_link_tokens ENABLE ROW LEVEL SECURITY;

-- ===== CONVERSATION_SUMMARIES TABLE POLICIES =====
CREATE POLICY "Users can view own summaries" ON public.conversation_summaries
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own summaries" ON public.conversation_summaries
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own summaries" ON public.conversation_summaries
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own summaries" ON public.conversation_summaries
  FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage summaries" ON public.conversation_summaries
  FOR ALL USING (auth.role() = 'service_role');

-- ===== SUBSCRIPTIONS TABLE POLICIES =====
CREATE POLICY "Users can view own subscription" ON public.subscriptions
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage subscriptions" ON public.subscriptions
  FOR ALL USING (auth.role() = 'service_role');

-- ===== SUBSCRIPTION_EVENTS TABLE POLICIES =====
CREATE POLICY "Users can view own subscription events" ON public.subscription_events
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage subscription events" ON public.subscription_events
  FOR ALL USING (auth.role() = 'service_role');
ALTER TABLE public.conversation_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscription_events ENABLE ROW LEVEL SECURITY;

-- Create a security definer function for safe user access
CREATE OR REPLACE FUNCTION public.get_current_user_id()
RETURNS uuid
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
STABLE
AS $$
  SELECT auth.uid();
$$;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT SELECT, INSERT, UPDATE ON public.users TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.auth_sessions TO authenticated;
GRANT SELECT, INSERT, UPDATE ON public.messages TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.message_feedback TO authenticated;
GRANT SELECT ON public.magic_link_tokens TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.conversation_summaries TO authenticated;
GRANT SELECT ON public.subscriptions TO authenticated;
GRANT SELECT ON public.subscription_events TO authenticated;

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON public.messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON public.messages(session_id);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id ON public.auth_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_message_feedback_user_id ON public.message_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_message_feedback_message_id ON public.message_feedback(message_id);
CREATE INDEX IF NOT EXISTS idx_conv_summaries_user_id ON public.conversation_summaries(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON public.subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscription_events_user_id ON public.subscription_events(user_id);