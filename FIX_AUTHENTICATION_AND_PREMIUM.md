# ?? FIX: Authentication & Premium Features Issue

## Issue Analysis

Your account `roboto.sai@outlook.com` shows as "not authenticated" and doesn't have premium features because:

1. **Missing Subscriptions Table** - No database table to store premium status
2. **No Premium Status Column** - auth.users table likely doesn't track subscription tier
3. **Payment System Not Fully Integrated** - Backend has payment routes but no subscription status storage

## ?? SECURITY NOTICE

**I cannot and will not access your actual Supabase database directly.** This would be a major security violation. Instead, I'll provide you with the SQL to run yourself.

## ?? Solution: Add Subscription Management

### Step 1: Create Subscriptions Table

Run this in your Supabase SQL Editor:

```sql
-- Subscriptions table for premium features
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    status TEXT DEFAULT 'inactive' CHECK (status IN ('active', 'inactive', 'canceled', 'past_due', 'trialing')),
    tier TEXT DEFAULT 'free' CHECK (tier IN ('free', 'premium', 'enterprise')),
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_customer ON subscriptions(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);

-- Enable RLS
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view own subscription" ON subscriptions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Service role can manage subscriptions" ON subscriptions
    FOR ALL USING (true);

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
```

### Step 2: Grant Yourself Premium Access

**TEMPORARY MANUAL OVERRIDE** (Run in Supabase SQL Editor):

```sql
-- Find your user ID
SELECT id, email FROM auth.users WHERE email = 'roboto.sai@outlook.com';

-- Insert premium subscription (replace YOUR_USER_ID with the ID from above)
INSERT INTO subscriptions (user_id, status, tier, current_period_start, current_period_end)
VALUES (
    'YOUR_USER_ID',  -- ? Replace with your actual user ID
    'active',
    'premium',
    NOW(),
    NOW() + INTERVAL '1 year'
)
ON CONFLICT (user_id) DO UPDATE SET
    status = 'active',
    tier = 'premium',
    current_period_start = NOW(),
    current_period_end = NOW() + INTERVAL '1 year';
```

### Step 3: Update Backend to Check Subscriptions

Add this to `backend/main.py`:

```python
async def get_user_subscription(user_id: str) -> dict:
    """Get user's subscription status"""
    supabase = get_supabase_client()
    if not supabase:
        return {"tier": "free", "status": "inactive"}
    
    try:
        result = await run_supabase_async(
            lambda: supabase.table("subscriptions")
            .select("*")
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        if result.data:
            return result.data
    except:
        pass
    
    return {"tier": "free", "status": "inactive"}

@app.get("/api/me")
async def get_current_user_info(current_user: Dict = Depends(get_current_user)):
    """Get current user info including subscription"""
    user_id = current_user["id"]
    subscription = await get_user_subscription(user_id)
    
    return {
        "user": current_user,
        "subscription": subscription,
        "is_premium": subscription.get("tier") in ["premium", "enterprise"] and subscription.get("status") == "active"
    }
```

### Step 4: Update Frontend to Use Premium Status

Update `src/stores/authStore.ts`:

```typescript
interface AuthState {
  // ... existing fields ...
  isPremium: boolean;
  subscriptionTier: 'free' | 'premium' | 'enterprise';
  
  // ... existing methods ...
}

// In refreshSession function, after setting user:
// Fetch subscription status
const { data: subData } = await supabase
  .from('subscriptions')
  .select('*')
  .eq('user_id', user.id)
  .single();

const isPremium = subData?.tier in ['premium', 'enterprise'] && subData?.status === 'active';

set({
  userId: user.id,
  username: user.user_metadata?.display_name || user.email?.split('@')[0] || 'User',
  email: user.email || null,
  avatarUrl: user.user_metadata?.avatar_url || null,
  provider: user.app_metadata?.provider || null,
  isLoggedIn: true,
  isPremium: isPremium,
  subscriptionTier: subData?.tier || 'free'
});
```

## ?? Quick Fix for Right Now

**To immediately grant yourself premium access:**

1. **Go to Supabase Dashboard**: https://supabase.com/dashboard/project/qlvzyqzrzbffmpbjtagj

2. **Open SQL Editor**

3. **Run This Query**:
```sql
-- Step 1: Find your user ID
SELECT id, email FROM auth.users WHERE email = 'roboto.sai@outlook.com';

-- Step 2: Create subscriptions table if it doesn't exist
-- (Run the CREATE TABLE from Step 1 above)

-- Step 3: Grant yourself premium (replace with your actual user_id from Step 1)
INSERT INTO subscriptions (user_id, status, tier, current_period_start, current_period_end)
VALUES (
    'PASTE_YOUR_USER_ID_HERE',
    'active',
    'premium',
    NOW(),
    NOW() + INTERVAL '10 years'
);
```

## ?? Verify It Works

After running the SQL:

```sql
-- Check your subscription
SELECT s.*, u.email 
FROM subscriptions s
JOIN auth.users u ON u.id = s.user_id
WHERE u.email = 'roboto.sai@outlook.com';
```

Should show:
- status: 'active'
- tier: 'premium'
- current_period_end: (far in the future)

## ?? Authentication Check

If you're still showing as "not authenticated":

```sql
-- Check if you exist in auth.users
SELECT id, email, created_at, confirmed_at 
FROM auth.users 
WHERE email = 'roboto.sai@outlook.com';

-- Check if email is confirmed
UPDATE auth.users 
SET confirmed_at = NOW(), 
    email_confirmed_at = NOW()
WHERE email = 'roboto.sai@outlook.com' 
  AND confirmed_at IS NULL;
```

## ?? Files to Modify (After Running SQL)

1. **Add subscription migration**: `supabase/migrations/002_add_subscriptions.sql` (content from Step 1)

2. **Update backend**: `backend/main.py` (add get_user_subscription function)

3. **Update frontend**: `src/stores/authStore.ts` (add isPremium field)

4. **Update checks**: Any component checking for premium features

## ?? Important Notes

1. **Never share your Supabase service role key** - I don't need it and shouldn't have it
2. **Run SQL in Supabase dashboard** - Don't paste your keys anywhere
3. **Backup first**: Export your database before major changes
4. **Test in staging**: If you have a staging environment, test there first

## ?? Security Best Practices

- ? Use RLS policies (Row Level Security)
- ? Keep service role key secret
- ? Never expose anon key in public repos (yours is in .env.example - that's OK)
- ? Validate subscription status server-side
- ? Don't trust client-side premium checks

---

**Quick Summary for You**:
1. Run the SQL in Steps 1 & 2 in your Supabase SQL Editor
2. Replace `YOUR_USER_ID` with your actual user ID
3. Your account will have premium features immediately
4. Then implement the backend/frontend changes for permanent solution

Let me know if you need any clarification!
