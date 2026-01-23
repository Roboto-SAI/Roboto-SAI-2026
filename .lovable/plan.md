
Goal: Add “Sign in with Google” + “Magic link” authentication to the existing home-page login UI, using your existing FastAPI + LangChain SQLite DB (“langchain db”) instead of Supabase, while keeping the app working in Docker and locally.

What I found in the current codebase
- Frontend auth is currently a client-side mock (`src/stores/authStore.ts`) that derives `userId` from a username and persists it in localStorage.
- Backend already exists (FastAPI) and already persists chat messages (LangChain history) into SQLite (`backend/models.py` `Message` table, `backend/langchain_memory.py`), and already proxies xAI voice WebSocket.
- There are no auth endpoints yet in the backend and no user/profile tables yet.
- Your chat endpoint already supports `user_id` and `session_id` fields; we will wire those to the authenticated user id.

Key decisions
- Authentication backend: FastAPI + SQLite (same DB as LangChain messages).
- Profile storage: Yes (per your selection). We’ll add a `users` table (profiles) in the same SQLite DB.
- Auth methods: Google OAuth + Magic link (passwordless).
- Session mechanism: Use httpOnly cookie sessions (preferred) so the frontend doesn’t store long-lived secrets in localStorage.
  - Frontend will call `/api/auth/me` to learn who is logged in.
  - Frontend will call `/api/auth/logout` to clear session.
  - All fetches to backend that require auth will use `credentials: "include"`.

Implementation outline (backend)
1) Add database models for auth
   - Create a new SQLAlchemy model `User` in `backend/models.py`:
     - `id` (uuid or random string primary key)
     - `email` (unique index)
     - `display_name`
     - `avatar_url`
     - `provider` (e.g., "google")
     - `provider_sub` (Google subject id)
     - `created_at`
   - Add `AuthSession` table:
     - `id` (opaque session id, primary key)
     - `user_id` (FK to User)
     - `created_at`, `expires_at`
   - Add `MagicLinkToken` table:
     - `token_hash` (primary/unique)
     - `email`
     - `user_id` (nullable until user created/linked)
     - `expires_at`, `used_at`
   - Update `backend/db.py:init_db()` to `create_all` these tables and (optionally) basic “ALTER TABLE” compatibility for existing db files.

2) Add Google OAuth endpoints (FastAPI)
   Add endpoints in `backend/main.py` (or a new `backend/auth.py` router, then include it):
   - `GET /api/auth/google/start`
     - Builds Google OAuth URL (using client_id, redirect_uri, scopes).
     - Sets a CSRF `state` value in a short-lived cookie.
     - Redirects the browser to Google.
   - `GET /api/auth/google/callback`
     - Validates `state` against cookie.
     - Exchanges `code` for tokens (server-to-server) and fetches Google userinfo (email, name, picture, sub).
     - Upserts the `User` row by `provider + provider_sub` (and/or email).
     - Creates an `AuthSession` row and sets an httpOnly cookie `roboto_session`.
     - Redirects to the frontend route `/chat` (or `/` with a “success” toast).

   Backend config (env vars needed):
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REDIRECT_URI` (ex: `http://localhost:5000/api/auth/google/callback`)
   - `FRONTEND_ORIGIN` (ex: `http://localhost:8080` or your preview URL)
   - `SESSION_SECRET` (used to sign cookie values if we choose signed cookies)
   - `SESSION_TTL_SECONDS` (optional)

   Dependencies likely needed in `backend/requirements.txt`:
   - `httpx` (HTTP requests to Google token + userinfo endpoints)
   - `python-multipart` (if any form posts later; optional)
   - Optionally `itsdangerous` (for signing cookies) or use server-stored opaque session id only.

3) Add Magic Link endpoints (FastAPI)
   - `POST /api/auth/magic/request` with body `{ email }`
     - Creates a one-time token, stores only a hash in DB, sets expiry (e.g., 15 minutes).
     - Sends email containing link to: `GET /api/auth/magic/verify?token=...`
     - Email sending approach:
       - If SMTP env vars are configured, send real email.
       - If not configured, log the magic link URL to backend logs so you can test without email provider.
   - `GET /api/auth/magic/verify?token=...`
     - Hash token, match DB row, ensure not expired/used.
     - Find or create `User` record by email.
     - Create `AuthSession`, set cookie, mark token used.
     - Redirect to `/chat`.

   Email provider env vars (later):
   - `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `EMAIL_FROM`
   (Or we can later switch to Resend/Mailgun/etc.)

4) Add session/auth helper endpoints & middleware
   - `GET /api/auth/me`
     - Reads session cookie, loads user, returns `{ user: { id, email, display_name, avatar_url } }` or 401.
   - `POST /api/auth/logout`
     - Deletes session record, clears cookie.
   - Add a small dependency function `get_current_user()` to reuse in protected endpoints.

5) Protect & integrate with existing chat endpoints
   - Update `/api/chat` to derive `user_id` from the authenticated session rather than trusting client-provided `user_id`.
     - Keep `session_id` from client so multiple conversations still work.
   - Update `/api/chat/history` similarly (use current user id).
   - This prevents someone from spoofing another user’s `user_id`.

6) CORS and cookies (critical for browser login)
   - Update CORS setup in `backend/main.py`:
     - Use `FRONTEND_ORIGIN` env var (and optionally an allowlist including your Lovable preview domain).
     - Keep `allow_credentials=True`.
   - Ensure frontend fetches use `credentials: "include"`.

Implementation outline (frontend)
7) Update auth state management to use backend session
   - Replace/extend `src/stores/authStore.ts`:
     - Store `user` object from `/api/auth/me` (id, email, display name, avatar).
     - Add async actions:
       - `refreshSession()` → calls `/api/auth/me`
       - `logout()` → POST `/api/auth/logout`
     - Keep a temporary fallback for old local username mode if backend is not reachable (optional), but default to backend auth once configured.

8) Update the home page Auth UI to include Google + Magic link
   - Update `src/components/auth/AuthForm.tsx`:
     - Add a “Continue with Google” button (opens `/api/auth/google/start` in same tab).
     - Add a “Send magic link” mode that only requires email:
       - On submit, call `POST /api/auth/magic/request`
       - Show toast “Check your email” (and for dev, mention link may appear in backend logs).
     - Keep the current register/login UI if you still want it visually, but it won’t be “real” until we implement password auth (out of scope for this request).

9) Ensure routing behaves like other chat apps
   - Update `src/pages/Chat.tsx`:
     - On mount, call `refreshSession()`.
     - If not authenticated, redirect to `/` and show a toast.
     - Use authenticated `user.id` as the `user_id` passed to the chat store, and stop passing spoofable user ids to backend.
   - Optionally update `src/pages/Index.tsx`:
     - If already authenticated, show “Continue as …” and a logout button.

Docker/backend startup fixes (so it actually runs)
10) Make backend container build reliable with new deps
   - Update `backend/requirements.txt` to include new required libraries (e.g., `httpx`, `itsdangerous`, SMTP library if needed).
   - Verify `backend/Dockerfile` still installs correctly.
   - Ensure `docker-compose.yml` passes required env vars (Google + session secrets).
   - Confirm the backend listens on the correct port (`5000`) and CORS includes the frontend origin.

11) Align frontend API base URL configuration
   - The frontend currently uses `VITE_API_URL` and `VITE_API_BASE_URL` in different places.
   - Standardize one approach (likely `VITE_API_BASE_URL=http://localhost:5000`) and ensure `Chat.tsx`, `chatStore.ts`, and voice mode use the same base.
   - Make sure all authenticated calls include `credentials: "include"`.

Testing checklist (acceptance criteria)
- Home page shows:
  - “Continue with Google” button that successfully signs in and redirects to `/chat`.
  - “Send magic link” that returns success (and email link is either sent or logged).
- `/api/auth/me` returns the current user when logged in; 401 otherwise.
- `/chat` route is protected (redirects to `/` if not logged in).
- Chat messages are persisted under the authenticated user id; history is correctly scoped per user.
- Docker: `docker compose --profile dev up` starts frontend and backend without runtime errors, and Google auth callback works with configured redirect URL.

Information I will need from you during implementation (blocking items)
- Your Google OAuth credentials:
  - Google Client ID + Client Secret
  - Authorized redirect URL you’ll use (local + eventually production)
- What domain/origin you want to treat as FRONTEND_ORIGIN for CORS:
  - Local dev (e.g., http://localhost:5173) and optionally the Lovable preview URL.
- For Magic Links: do you want real email sending now (provide SMTP/Resend), or is “log link to backend console” acceptable until you wire an email provider?

Files that will likely be changed/added (implementation scope)
Frontend:
- `src/components/auth/AuthForm.tsx`
- `src/pages/Index.tsx`
- `src/pages/Chat.tsx`
- `src/stores/authStore.ts`
- `src/config/index.ts` (optional cleanup)

Backend:
- `backend/main.py` (new auth routes + session helpers)
- `backend/models.py` (User/AuthSession/MagicLinkToken tables)
- `backend/db.py` (init/migrations-ish adjustments)
- `backend/requirements.txt` (new deps)
- `backend/Dockerfile` (only if system packages are needed)
- `docker-compose.yml` (env vars)

Notes on security
- We will not store roles on users/profiles (none are needed for this feature).
- We will not trust `user_id` coming from the browser; backend will derive it from the session cookie.
- Cookies will be httpOnly to reduce XSS token theft risk.

