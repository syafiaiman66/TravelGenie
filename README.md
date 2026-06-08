# Bounce

Bounce is an AI-powered travel itinerary planner. Users can sign in with Google, enter a destination, budget, currency, trip duration, number of travelers, travel interests, budget style, and places they want to visit. Bounce then uses an AI model to generate a practical day-by-day itinerary with activities, estimated costs, transportation guidance, food recommendations, and a budget breakdown.

The project was built as a lightweight full-stack web app using plain HTML, CSS, JavaScript, and Python. It runs with SQLite locally and can use Render PostgreSQL in production.

## Features

- Google OAuth login and session handling
- AI-powered itinerary generation
- Custom destination input, including places the user wants to visit
- Budget style options such as Student, Comfort, Luxury, Backpacker, and Family comfort
- User-selected currency for itinerary cost estimates
- Multi-day itinerary cards with times, activities, notes, and estimated prices
- Budget breakdown, transportation guidance, and food recommendations
- Saved and recent trip history in the browser
- Feedback form that can email customer messages to Bounce support
- Render deployment support with PostgreSQL

## Tech Stack

- Frontend: HTML, CSS, JavaScript
- Backend: Python `http.server`
- AI model: configurable travel-planning model
- Authentication: Google OAuth 2.0
- Local database: SQLite
- Production database: Render PostgreSQL
- Email feedback: SMTP

## Project Structure

```text
TravelGenie/
  app.js                 Frontend logic and itinerary rendering
  index.html             Main website UI
  styles.css             Website styling
  server.py              Python backend, auth, AI generation, feedback email
  render.yaml            Render deployment blueprint
  requirements.txt       Python dependencies
  .env.example           Example environment variables
  assets/
    bounce-logo.svg      Bounce logo used in the UI
```

## How It Works

1. The user logs in with Google.
2. The user fills in the trip form.
3. The browser sends the trip request to `/api/itinerary`.
4. The Python server sends a structured prompt to the AI model.
5. The AI model returns itinerary JSON.
6. The frontend renders the JSON as itinerary cards.

The AI model is expected to return this main JSON structure. The `schedule` array repeats for the number of days selected by the user, and each day should contain four activity items.

```json
{
  "destination": "Tokyo",
  "country": "Japan",
  "summary": "Short trip overview.",
  "transport": "One practical transport paragraph.",
  "food": [
    "Food recommendation 1",
    "Food recommendation 2",
    "Food recommendation 3"
  ],
  "breakdown": [
    { "label": "Accommodation", "percent": 35, "amount": 1050 },
    { "label": "Food", "percent": 20, "amount": 600 },
    { "label": "Transportation", "percent": 15, "amount": 450 },
    { "label": "Activities", "percent": 20, "amount": 600 },
    { "label": "Buffer", "percent": 10, "amount": 300 }
  ],
  "schedule": [
    {
      "day": 1,
      "title": "Arrival and city highlights",
      "items": [
        {
          "time": "08:30",
          "title": "Breakfast near the station",
          "notes": "Start the day with a simple meal and prepare transit cards.",
          "cost": {
            "raw": 25,
            "label": "USD 25"
          }
        },
        {
          "time": "10:30",
          "title": "Sensoji Temple",
          "notes": "Explore the temple grounds and browse snacks along Nakamise Street.",
          "cost": {
            "raw": 20,
            "label": "USD 20"
          }
        },
        {
          "time": "14:00",
          "title": "Tokyo Skytree",
          "notes": "Visit the observation deck and enjoy wide city views.",
          "cost": {
            "raw": 90,
            "label": "USD 90"
          }
        },
        {
          "time": "19:30",
          "title": "Dinner in Asakusa",
          "notes": "Try local ramen or tempura near the historic streets.",
          "cost": {
            "raw": 75,
            "label": "USD 75"
          }
        }
      ],
      "total": {
        "raw": 210,
        "label": "USD 210"
      }
    }
  ]
}
```

## Local Setup

1. Install Python.

2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Copy the environment template:

   ```powershell
   Copy-Item .env.example .env
   ```

4. Open `.env` and add your real credentials:

   ```env
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   GOOGLE_REDIRECT_URI=http://127.0.0.1:8000/auth/google/callback
   GEMINI_API_KEY=your-ai-api-key
   GEMINI_MODEL=gemini-2.5-flash
   ```

5. Start the server:

   ```powershell
   python server.py
   ```

6. Open the app:

   ```text
   http://127.0.0.1:8000/
   ```

## Google OAuth Setup

Create a Google OAuth client in Google Cloud Console.

For local development, add this authorized redirect URI:

```text
http://127.0.0.1:8000/auth/google/callback
```

For Render deployment, add this authorized redirect URI after your Render URL is created:

```text
https://YOUR-RENDER-SERVICE.onrender.com/auth/google/callback
```

## AI API Setup

Create an AI API key and add it to `.env` locally or Render environment variables in production:

```env
GEMINI_API_KEY=your-ai-api-key
GEMINI_MODEL=gemini-2.5-flash
```

## Feedback Email Setup

Bounce includes a feedback form where logged-in users can send inconvenience reports, bugs, or suggestions.

To enable email sending, configure SMTP:

```env
FEEDBACK_TO=bouncebtoe@gmail.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-sender-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SMTP_FROM=your-sender-email@gmail.com
```

If you use Gmail, `SMTP_PASSWORD` should be a Gmail app password, not your normal Gmail password.

## Environment Variables

| Variable | Purpose |
| --- | --- |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `GOOGLE_REDIRECT_URI` | OAuth callback URL |
| `GEMINI_API_KEY` | AI API key used by the itinerary generator |
| `GEMINI_MODEL` | AI model name used by the itinerary generator |
| `DATABASE_URL` | PostgreSQL connection string used on Render |
| `FEEDBACK_TO` | Email address that receives feedback |
| `SMTP_HOST` | SMTP server host |
| `SMTP_PORT` | SMTP server port |
| `SMTP_USERNAME` | Email account used to send feedback |
| `SMTP_PASSWORD` | SMTP password or app password |
| `SMTP_FROM` | Sender email address |
| `COOKIE_SECURE` | Use `true` in production with HTTPS |
| `HOST` | Server host, use `0.0.0.0` on Render |
| `PORT` | Server port, provided automatically by Render |

## Deploy On Render

This project includes `render.yaml`, so it can be deployed as a Render Blueprint.

1. Push the project to GitHub.
2. Create a new Render Blueprint from the repository.
3. Add the required environment variables in Render.
4. Deploy the service.
5. Add the Render callback URL to Google Cloud Console.

Render will provide `DATABASE_URL` automatically if the PostgreSQL database in `render.yaml` is created.

## Notes

- Do not commit `.env`.
- Keep API keys, OAuth secrets, and SMTP passwords private.
- The local SQLite database file is ignored by Git.
- The existing local SQLite filename is `travelgenie.sqlite3` for compatibility.
- The app name shown to users is Bounce.

## License

This project is for educational and prototype purposes.
