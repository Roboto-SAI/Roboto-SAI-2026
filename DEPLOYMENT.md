# Roboto SAI Deployment Guide for Render

## ?? CRITICAL FIXES APPLIED (Jan 31, 2026)

**Two critical runtime issues have been fixed:**

1. ? **Chat 503 Error Fixed** - Grok API now works with direct fallback
2. ? **Import Errors Fixed** - Module paths corrected for PYTHONPATH

**See `CRITICAL_RUNTIME_FIXES.md` for details**

## ?? CRITICAL: render.yaml Must Include dockerContext

**The #1 cause of deployment failures is missing `dockerContext` in render.yaml!**

Ensure your `render.yaml` backend service includes:
```yaml
dockerfilePath: ./backend/Dockerfile
dockerContext: ./backend  # ? CRITICAL: Must be set!
```

## Prerequisites

1. **Supabase Project**
   - Create a Supabase project at https://supabase.com
   - Run the migration: `supabase/migrations/001_knowledge_base_schema.sql`
   - Get your:
     - Project URL (`SUPABASE_URL`)
     - Anon Key (`SUPABASE_ANON_KEY`)
     - Service Role Key (`SUPABASE_SERVICE_ROLE_KEY`)

2. **xAI Grok API Key**
   - Get your API key from https://x.ai
   - Set as `XAI_API_KEY`

## Render Configuration

### Backend Service (roboto-sai-backend)

Environment Variables to set in Render Dashboard:
```
XAI_API_KEY=your_xai_api_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
FRONTEND_ORIGIN=https://roboto-sai-frontend.onrender.com
FRONTEND_HASH_ROUTER=true
PYTHON_ENV=production
SESSION_TTL_SECONDS=2592000
COOKIE_SECURE=true
COOKIE_SAMESITE=none
```

### Frontend Service (roboto-sai-frontend)

Environment Variables to set in Render Dashboard:
```
VITE_API_BASE_URL=https://roboto-sai-backend.onrender.com
VITE_API_URL=https://roboto-sai-backend.onrender.com
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
NODE_ENV=production
```

## Deployment Steps

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Production-ready deployment"
   git push origin main
   ```

2. **Render Will Auto-Deploy**
   - Backend will build from `backend/Dockerfile`
   - Frontend will build from root `Dockerfile`
   - Health checks at `/api/health` and `/health`

3. **Verify Deployment**
   - Check backend: https://roboto-sai-backend.onrender.com/health
   - Check frontend: https://roboto-sai-frontend.onrender.com
   - Test login and chat functionality

## Troubleshooting

### Backend Fails to Start
- Check Render logs for import errors
- Verify all environment variables are set
- Check Supabase connection
- If you see "constraints.txt not found": This is fixed in latest Dockerfile (removed constraints.txt requirement)

### Backend Docker Build Fails
- **Error: "requirements.txt not found" or "constraints.txt not found"**
  - ? **FIXED**: Ensure `dockerContext: ./backend` is set in render.yaml (THIS IS THE FIX!)
  - Verify `dockerfilePath: ./backend/Dockerfile` in render.yaml
  - Check that `backend/requirements.txt` exists in your repo
  - The Dockerfile now works without constraints.txt
- **Error: "roboto-sai-sdk" fails to install**
  - SDK is optional - build will continue
  - Verify your repo has access to the SDK GitHub repo if needed
- **Error: Module import errors after build**
  - Verify `PYTHONPATH=/app` in render.yaml (not `/app/backend`)

### Frontend Fails to Build
- Verify `VITE_SUPABASE_URL` is set during build
- Check npm install succeeds
- Review build logs for TypeScript errors

### CORS Errors
- Ensure `FRONTEND_ORIGIN` in backend matches your frontend URL
- Verify `COOKIE_SAMESITE=none` and `COOKIE_SECURE=true` are set

### Memory System Not Working
- Verify Supabase migration was run
- Check RLS policies are enabled
- Verify user is authenticated

## Custom Domain (Optional)

1. Add custom domain in Render dashboard
2. Update `FRONTEND_ORIGIN` to include custom domain
3. Update CORS settings if needed

## Monitoring

- Render provides logs and metrics
- Health check endpoint: `/api/health`
- Monitor Supabase dashboard for database performance
