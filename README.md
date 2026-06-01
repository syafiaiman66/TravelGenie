# TravelGenie

TravelGenie is a travel itinerary planning prototype with server-side Google OAuth 2.0 sign-in.

## Run Locally

1. Create a Google OAuth client in Google Cloud Console.
2. Add this authorized redirect URI:

   `http://127.0.0.1:8000/auth/google/callback`

3. Copy `.env.example` to `.env`, then put your Google credentials in `.env`.
4. Start the app:

   ```powershell
   python server.py
   ```

5. Open:

   `http://127.0.0.1:8000/`

The app stores verified Google users and sessions in `travelgenie.sqlite3`. Google client secrets stay on the server and are never exposed to browser JavaScript.

## Deploy On Render

This project is a custom Python `http.server` app, not Flask, FastAPI, Django, Node, or React.

Use `render.yaml` as a Render Blueprint. Add these environment variables in Render:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `COOKIE_SECURE=true`
- `HOST=0.0.0.0`
- `DATA_DIR=/var/data`

After Render creates the service, set `GOOGLE_REDIRECT_URI` to:

`https://YOUR-RENDER-SERVICE.onrender.com/auth/google/callback`

Add the same URL to Google Cloud Console as an authorized redirect URI.