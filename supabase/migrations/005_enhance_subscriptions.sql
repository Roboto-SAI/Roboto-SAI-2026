BEGIN;

ALTER TABLE subscriptions
    ADD COLUMN IF NOT EXISTS trial_started_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS canceled_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS cancel_reason TEXT,
    ADD COLUMN IF NOT EXISTS previous_tier TEXT;

CREATE TABLE IF NOT EXISTS subscription_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subscription_id UUID REFERENCES subscriptions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK (event_type IN (
        'created', 'activated', 'canceled', 'reactivated',
        'upgraded', 'downgraded', 'trial_started', 'trial_ended',
        'payment_failed', 'payment_succeeded'
    )),
    from_status TEXT,
    to_status TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_subscription_events_user_id ON subscription_events(user_id);
CREATE INDEX IF NOT EXISTS idx_subscription_events_subscription_id ON subscription_events(subscription_id);
CREATE INDEX IF NOT EXISTS idx_subscription_events_created_at ON subscription_events(created_at DESC);

ALTER TABLE subscription_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own subscription events" ON subscription_events
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage subscription events" ON subscription_events
    FOR ALL USING (auth.role() = 'service_role');

CREATE OR REPLACE FUNCTION log_subscription_event(
    p_subscription_id UUID,
    p_user_id UUID,
    p_event_type TEXT,
    p_from_status TEXT DEFAULT NULL,
    p_to_status TEXT DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}'
) RETURNS UUID AS $$
DECLARE
    event_id UUID;
BEGIN
    INSERT INTO subscription_events (
        subscription_id, user_id, event_type,
        from_status, to_status, metadata
    ) VALUES (
        p_subscription_id, p_user_id, p_event_type,
        p_from_status, p_to_status, p_metadata
    ) RETURNING id INTO event_id;

    RETURN event_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION log_subscription_event TO authenticated;

COMMIT;
