-- Subscriptions & Premium Features Schema
-- Created for Roboto SAI Premium Features
-- Run this after 001_knowledge_base_schema.sql

-- Subscriptions table for managing premium access
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
    stripe_customer_id TEXT UNIQUE,
    stripe_subscription_id TEXT UNIQUE,
    status TEXT DEFAULT 'inactive' CHECK (status IN ('active', 'inactive', 'canceled', 'past_due', 'trialing')),
    tier TEXT DEFAULT 'free' CHECK (tier IN ('free', 'premium', 'enterprise')),
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    trial_end TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_customer ON subscriptions(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_subscription ON subscriptions(stripe_subscription_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_tier ON subscriptions(tier);
CREATE INDEX IF NOT EXISTS idx_subscriptions_period_end ON subscriptions(current_period_end);

-- Enable RLS
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view own subscription" ON subscriptions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage subscriptions" ON subscriptions
    FOR ALL USING (auth.role() = 'service_role');

-- Function to check if subscription is active
CREATE OR REPLACE FUNCTION is_subscription_active(sub_user_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    sub_record RECORD;
BEGIN
    SELECT status, tier, current_period_end
    INTO sub_record
    FROM subscriptions
    WHERE user_id = sub_user_id;
    
    IF NOT FOUND THEN
        RETURN FALSE;
    END IF;
    
    RETURN (
        sub_record.status = 'active' AND
        sub_record.tier IN ('premium', 'enterprise') AND
        (sub_record.current_period_end IS NULL OR sub_record.current_period_end > NOW())
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to auto-update updated_at
CREATE OR REPLACE FUNCTION update_subscriptions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_subscriptions_timestamp
    BEFORE UPDATE ON subscriptions
    FOR EACH ROW
    EXECUTE FUNCTION update_subscriptions_updated_at();

-- Usage tracking for premium features (optional)
CREATE TABLE IF NOT EXISTS feature_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    feature_name TEXT NOT NULL,
    usage_count INTEGER DEFAULT 1,
    last_used TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_feature_usage_user_id ON feature_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_feature_usage_feature ON feature_usage(feature_name);

-- Enable RLS
ALTER TABLE feature_usage ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own usage" ON feature_usage
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage usage" ON feature_usage
    FOR ALL USING (auth.role() = 'service_role');

-- View for easy subscription checking
CREATE OR REPLACE VIEW user_subscription_status AS
SELECT 
    u.id as user_id,
    u.email,
    COALESCE(s.tier, 'free') as tier,
    COALESCE(s.status, 'inactive') as status,
    s.current_period_end,
    is_subscription_active(u.id) as is_active,
    s.stripe_customer_id,
    s.stripe_subscription_id
FROM auth.users u
LEFT JOIN subscriptions s ON s.user_id = u.id;

-- Grant access to view
GRANT SELECT ON user_subscription_status TO authenticated;

-- Comments for documentation
COMMENT ON TABLE subscriptions IS 'Manages user subscription status and premium features access';
COMMENT ON COLUMN subscriptions.status IS 'Subscription status: active, inactive, canceled, past_due, trialing';
COMMENT ON COLUMN subscriptions.tier IS 'Subscription tier: free, premium, enterprise';
COMMENT ON FUNCTION is_subscription_active IS 'Helper function to check if a user has an active premium subscription';
