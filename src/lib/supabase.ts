/**/**






























export type { SupabaseClient };export { supabase };}  supabase = (window as any).__supabaseInstance;  // eslint-disable-next-line @typescript-eslint/no-explicit-any  }    });      },        detectSessionInUrl: true,        autoRefreshToken: true,        persistSession: true,      auth: {    (window as any).__supabaseInstance = createClient(supabaseUrl, supabaseKey, {    // eslint-disable-next-line @typescript-eslint/no-explicit-any  if (!(window as any).__supabaseInstance) {  // eslint-disable-next-line @typescript-eslint/no-explicit-anyif (supabaseUrl && supabaseKey && typeof window !== 'undefined') {let supabase: SupabaseClient | null = null;const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY;const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;import { createClient, SupabaseClient } from '@supabase/supabase-js'; */ * Created by Roberto Villarreal Martinez for Roboto SAI * Ensures only one GoTrueClient instance exists in the browser context. * Shared Supabase Client Singleton * Shared Supabase Client Singleton
 * Ensures only one GoTrueClient instance exists in the browser context.
 */
import { createClient, SupabaseClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

let supabase: SupabaseClient | null = null;

if (supabaseUrl && supabaseKey && typeof window !== 'undefined') {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  if (!(window as any).__supabaseInstance) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (window as any).__supabaseInstance = createClient(supabaseUrl, supabaseKey, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
      },
    });
  }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  supabase = (window as any).__supabaseInstance;
}

export { supabase };
export type { SupabaseClient };
