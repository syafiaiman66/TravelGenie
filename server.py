import hashlib
import json
import os
import secrets
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from http import HTTPStatus
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SESSION_DAYS = 7
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


def load_env_file():
    env_path = ROOT / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_env_file()
DATABASE_URL = os.environ.get("DATABASE_URL")
USE_POSTGRES = bool(DATABASE_URL)
if USE_POSTGRES:
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as exc:
        raise RuntimeError("DATABASE_URL is set, but psycopg is not installed.") from exc
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    SQL_PARAM = "%s"
else:
    DATA_DIR = Path(os.environ.get("DATA_DIR", str(ROOT))).resolve()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    DB_PATH = DATA_DIR / "travelgenie.sqlite3"
    SQL_PARAM = "?"
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8000"))


def connect_db():
    if USE_POSTGRES:
        return psycopg.connect(DATABASE_URL, row_factory=dict_row)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    user_id_column = "SERIAL PRIMARY KEY" if USE_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"
    with connect_db() as conn:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS users (
                id {user_id_column},
                google_user_id TEXT UNIQUE,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                profile_picture TEXT,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at INTEGER NOT NULL,
                created_at INTEGER NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )


def now():
    return int(time.time())


def cookie_header(name, value, max_age, http_only=True):
    parts = [f"{name}={value}", "Path=/", "SameSite=Lax", f"Max-Age={max_age}"]
    if http_only:
        parts.append("HttpOnly")
    if os.environ.get("COOKIE_SECURE", "").lower() == "true":
        parts.append("Secure")
    return "; ".join(parts)


def token_hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def json_bytes(payload):
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


class GeminiGenerationError(Exception):
    pass


ITINERARY_RESPONSE_SCHEMA = {
    "type": "object",
    "description": "A complete multi-day travel itinerary for the requested trip.",
    "properties": {
        "destination": {"type": "string", "description": "Destination city, town, island, or region."},
        "country": {"type": "string", "description": "Country where the destination is located."},
        "summary": {"type": "string", "description": "One concise overview of the trip plan."},
        "transport": {"type": "string", "description": "Practical transport guidance as one readable paragraph."},
        "food": {
            "type": "array",
            "description": "Three local food recommendations as plain strings.",
            "minItems": 3,
            "maxItems": 3,
            "items": {"type": "string"},
        },
        "breakdown": {
            "type": "array",
            "description": "Budget categories as an array, never an object/map.",
            "minItems": 5,
            "maxItems": 5,
            "items": {
                "type": "object",
                "properties": {
                    "label": {
                        "type": "string",
                        "enum": ["Accommodation", "Food", "Transportation", "Activities", "Buffer"],
                        "description": "One required budget category.",
                    },
                    "percent": {"type": "number", "description": "Percentage of the total budget."},
                    "amount": {"type": "number", "description": "Budget amount in the requested currency."},
                },
                "required": ["label", "percent", "amount"],
                "propertyOrdering": ["label", "percent", "amount"],
            },
        },
        "schedule": {
            "type": "array",
            "description": "One object per trip day. The array length must equal the requested days.",
            "items": {
                "type": "object",
                "properties": {
                    "day": {"type": "integer", "description": "Day number starting at 1."},
                    "title": {"type": "string", "description": "Unique theme for this day."},
                    "items": {
                        "type": "array",
                        "description": "Exactly four varied activity objects for this day.",
                        "minItems": 4,
                        "maxItems": 4,
                        "items": {
                            "type": "object",
                            "properties": {
                                "time": {"type": "string", "description": "Specific time like 08:30, 10:30, 14:00, 19:30."},
                                "title": {"type": "string", "description": "Specific activity or place name."},
                                "notes": {"type": "string", "description": "One practical activity description."},
                                "cost": {
                                    "type": "object",
                                    "properties": {
                                        "raw": {"type": "number", "description": "Estimated activity cost in requested currency."},
                                        "label": {"type": "string", "description": "Formatted cost using the requested currency symbol or code."},
                                    },
                                    "required": ["raw", "label"],
                                    "propertyOrdering": ["raw", "label"],
                                },
                            },
                            "required": ["time", "title", "notes", "cost"],
                            "propertyOrdering": ["time", "title", "notes", "cost"],
                        },
                    },
                    "total": {
                        "type": "object",
                        "properties": {
                            "raw": {"type": "number", "description": "Total estimated cost for this day."},
                            "label": {"type": "string", "description": "Formatted total in requested currency."},
                        },
                        "required": ["raw", "label"],
                        "propertyOrdering": ["raw", "label"],
                    },
                },
                "required": ["day", "title", "items", "total"],
                "propertyOrdering": ["day", "title", "items", "total"],
            },
        },
    },
    "required": ["destination", "country", "summary", "transport", "food", "breakdown", "schedule"],
    "propertyOrdering": ["destination", "country", "summary", "transport", "food", "breakdown", "schedule"],
}


def strip_json_fence(text):
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    return cleaned


def parse_itinerary_json(text):
    cleaned = strip_json_fence(text)
    attempts = [cleaned]

    if not cleaned.startswith("{") and '"destination"' in cleaned:
        attempts.append("{" + cleaned.rstrip().rstrip(",") + "}")

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        attempts.append(cleaned[start : end + 1])

    last_error = None
    for candidate in attempts:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            last_error = exc

    raise last_error or json.JSONDecodeError("Invalid JSON", cleaned, 0)


def json_error_summary(detail):
    try:
        payload = json.loads(detail)
        message = payload.get("error", {}).get("message")
        if message:
            return message
    except json.JSONDecodeError:
        pass
    return detail[:280] if detail else "Gemini did not return an error message."


class TravelGenieHandler(SimpleHTTPRequestHandler):
    server_version = "TravelGenie/1.0"

    def translate_path(self, path):
        path = urllib.parse.urlparse(path).path
        if path == "/":
            path = "/index.html"
        return str(ROOT / path.lstrip("/"))

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        super().end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/session":
            self.handle_session()
            return
        if parsed.path == "/auth/google":
            self.handle_google_start()
            return
        if parsed.path == "/auth/google/callback":
            self.handle_google_callback(parsed)
            return
        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/itinerary":
            self.handle_generate_itinerary()
            return
        if parsed.path == "/auth/logout":
            self.handle_logout()
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def read_cookies(self):
        cookie = SimpleCookie()
        cookie.load(self.headers.get("Cookie", ""))
        return {key: morsel.value for key, morsel in cookie.items()}

    def send_json(self, payload, status=HTTPStatus.OK, extra_headers=None):
        body = json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        if extra_headers:
            for key, value in extra_headers:
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw_body = self.rfile.read(length).decode("utf-8")
        return json.loads(raw_body)

    def redirect(self, location, extra_headers=None):
        self.send_response(HTTPStatus.FOUND)
        self.send_header("Location", location)
        if extra_headers:
            for key, value in extra_headers:
                self.send_header(key, value)
        self.end_headers()

    def get_redirect_uri(self):
        configured_uri = os.environ.get("GOOGLE_REDIRECT_URI")
        if configured_uri:
            return configured_uri

        host = self.headers.get("X-Forwarded-Host") or self.headers.get("Host")
        if host:
            proto = self.headers.get("X-Forwarded-Proto", "http")
            return f"{proto}://{host}/auth/google/callback"

        return f"http://127.0.0.1:{PORT}/auth/google/callback"

    def get_session_user(self):
        token = self.read_cookies().get("tg_session")
        if not token:
            return None

        hashed = token_hash(token)
        with connect_db() as conn:
            row = conn.execute(
                f"""
                SELECT users.id, users.google_user_id, users.full_name, users.email, users.profile_picture
                FROM sessions
                JOIN users ON users.id = sessions.user_id
                WHERE sessions.token_hash = {SQL_PARAM} AND sessions.expires_at > {SQL_PARAM}
                """,
                (hashed, now()),
            ).fetchone()
        if not row:
            return None
        return dict(row)

    def handle_session(self):
        user = self.get_session_user()
        if not user:
            self.send_json({"authenticated": False})
            return

        self.send_json(
            {
                "authenticated": True,
                "user": {
                    "id": user["id"],
                    "googleUserId": user["google_user_id"],
                    "fullName": user["full_name"],
                    "email": user["email"],
                    "profilePicture": user["profile_picture"],
                },
            }
        )

    def handle_google_start(self):
        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")
        if not client_id or not client_secret:
            self.redirect("/?auth_error=missing_google_config")
            return

        state = secrets.token_urlsafe(32)
        params = {
            "client_id": client_id,
            "redirect_uri": self.get_redirect_uri(),
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "prompt": "select_account",
            "include_granted_scopes": "true",
        }
        headers = [("Set-Cookie", cookie_header("tg_oauth_state", state, 600))]
        self.redirect(f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}", headers)

    def handle_google_callback(self, parsed):
        query = urllib.parse.parse_qs(parsed.query)
        if "error" in query:
            self.redirect("/?auth_error=google_cancelled")
            return

        code = query.get("code", [""])[0]
        returned_state = query.get("state", [""])[0]
        stored_state = self.read_cookies().get("tg_oauth_state")
        clear_state = ("Set-Cookie", cookie_header("tg_oauth_state", "", 0))

        if not code or not stored_state or not secrets.compare_digest(returned_state, stored_state):
            self.redirect("/?auth_error=invalid_oauth_state", [clear_state])
            return

        try:
            token_payload = self.exchange_code_for_token(code)
            userinfo = self.fetch_google_userinfo(token_payload["access_token"])
            user_id = self.upsert_user(userinfo)
            session_token = self.create_session(user_id)
        except Exception:
            self.redirect("/?auth_error=google_auth_failed", [clear_state])
            return

        headers = [
            clear_state,
            ("Set-Cookie", cookie_header("tg_session", session_token, SESSION_DAYS * 24 * 60 * 60)),
        ]
        self.redirect("/?auth=success#planner", headers)

    def exchange_code_for_token(self, code):
        data = urllib.parse.urlencode(
            {
                "code": code,
                "client_id": os.environ["GOOGLE_CLIENT_ID"],
                "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
                "redirect_uri": self.get_redirect_uri(),
                "grant_type": "authorization_code",
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            GOOGLE_TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=12) as response:
            return json.loads(response.read().decode("utf-8"))

    def fetch_google_userinfo(self, access_token):
        request = urllib.request.Request(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        with urllib.request.urlopen(request, timeout=12) as response:
            userinfo = json.loads(response.read().decode("utf-8"))

        if not userinfo.get("sub") or not userinfo.get("email") or not userinfo.get("email_verified"):
            raise ValueError("Google account is not verified")
        return userinfo

    def handle_generate_itinerary(self):
        if not self.get_session_user():
            self.send_json({"error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
            return

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            self.send_json({"error": "missing_gemini_config"}, HTTPStatus.SERVICE_UNAVAILABLE)
            return

        try:
            trip_request = self.read_json_body()
            itinerary = self.generate_itinerary_with_gemini(trip_request, api_key)
        except ValueError as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        except GeminiGenerationError as exc:
            self.send_json({"error": "gemini_generation_failed", "detail": str(exc)}, HTTPStatus.BAD_GATEWAY)
            return
        except Exception as exc:
            print(f"Gemini generation error: {exc!r}", file=sys.stderr, flush=True)
            self.send_json(
                {"error": "gemini_generation_failed", "detail": "The server could not read Gemini's response."},
                HTTPStatus.BAD_GATEWAY,
            )
            return

        self.send_json({"itinerary": itinerary})

    def generate_itinerary_with_gemini(self, trip_request, api_key):
        prompt = self.build_itinerary_prompt(trip_request)
        gemini_payload = self.request_gemini(prompt, api_key)
        return self.parse_gemini_itinerary(gemini_payload)

    def request_gemini(self, prompt, api_key):
        generation_config = {
            "temperature": 0.35,
            "responseMimeType": "application/json",
            "responseJsonSchema": ITINERARY_RESPONSE_SCHEMA,
            "maxOutputTokens": 16384,
        }

        request_payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": generation_config,
        }
        url = GEMINI_API_URL.format(model=urllib.parse.quote(GEMINI_MODEL))
        started_at = time.monotonic()
        print(f"Gemini request started for {GEMINI_MODEL}", file=sys.stderr, flush=True)
        request = urllib.request.Request(
            url,
            data=json_bytes(request_payload),
            headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                payload = json.loads(response.read().decode("utf-8"))
                elapsed = time.monotonic() - started_at
                print(f"Gemini request finished in {elapsed:.1f}s", file=sys.stderr, flush=True)
                return payload
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            summary = json_error_summary(detail)
            print(f"Gemini API HTTP error {exc.code}: {detail}", file=sys.stderr, flush=True)
            raise GeminiGenerationError(f"Gemini API error {exc.code}: {summary}") from exc
        except urllib.error.URLError as exc:
            print(f"Gemini network error: {exc!r}", file=sys.stderr, flush=True)
            raise GeminiGenerationError(f"Could not reach Gemini: {exc.reason}") from exc

    def parse_gemini_itinerary(self, gemini_payload):
        prompt_feedback = gemini_payload.get("promptFeedback") or {}
        if prompt_feedback.get("blockReason"):
            raise GeminiGenerationError(f"Gemini blocked the prompt: {prompt_feedback['blockReason']}.")

        candidate = (gemini_payload.get("candidates") or [{}])[0]
        content = candidate.get("content") or {}
        parts = content.get("parts") or []
        text = "".join(part.get("text", "") for part in parts).strip()
        if not text:
            finish_reason = candidate.get("finishReason", "unknown")
            raise GeminiGenerationError(f"Gemini returned no itinerary text. Finish reason: {finish_reason}.")

        try:
            return parse_itinerary_json(text)
        except json.JSONDecodeError as exc:
            print(f"Gemini returned non-JSON text: {text[:1000]}", file=sys.stderr, flush=True)
            raise GeminiGenerationError("Gemini returned text that was not valid itinerary JSON.") from exc

    def build_itinerary_prompt(self, trip_request):
        required = ["destination", "budget", "currency", "travelers", "days", "budgetStyle"]
        missing = [key for key in required if not trip_request.get(key)]
        if missing:
            raise ValueError(f"Missing required trip fields: {', '.join(missing)}")

        destination = str(trip_request["destination"]).strip()
        budget = float(trip_request["budget"])
        travelers = int(trip_request["travelers"])
        days = int(trip_request["days"])
        if budget <= 0 or travelers <= 0 or days <= 0:
            raise ValueError("Budget, travelers, and days must be greater than zero.")

        prompt_payload = {
            "destination": destination,
            "totalBudget": budget,
            "currency": str(trip_request["currency"]).strip(),
            "travelers": travelers,
            "days": min(days, 21),
            "tripName": str(trip_request.get("tripName") or "").strip(),
            "interests": trip_request.get("interests") or [],
            "placesUserWants": trip_request.get("customPlaces") or [],
            "budgetStyle": str(trip_request["budgetStyle"]).strip(),
        }

        return f"""
You are TravelGenie. Generate one complete travel itinerary that matches the provided JSON schema.

TRIP_PARAMETERS:
{json.dumps(prompt_payload, ensure_ascii=False)}

OUTPUT_CONTRACT:
Return exactly one JSON object with these top-level keys only:
destination, country, summary, transport, food, breakdown, schedule.
The JSON schema is mandatory. Do not invent, rename, omit, or flatten fields.

FIELD_RULES:
- destination: string. Use the normalized destination name.
- country: string. Use the destination country.
- summary: string. One useful trip overview, maximum 25 words.
- transport: string. One practical paragraph, maximum 45 words. Do not return an object.
- food: array of exactly 3 strings. Local food or restaurant-style recommendations.
- breakdown: array of exactly 5 objects. Never return an object/map.
- breakdown labels must be exactly: Accommodation, Food, Transportation, Activities, Buffer.
- schedule: array with exactly TRIP_PARAMETERS.days day objects.
- Each day object must have day, title, items, total.
- Each day items array must contain exactly 4 activity objects.
- The 4 activity objects must represent breakfast/arrival, morning, afternoon, evening.
- Every activity must have time, title, notes, cost.
- time must be specific, for example 08:30, 10:30, 14:00, 19:30.
- title must name a real place, meal, route, or activity.
- notes must describe what the traveler does, 8 to 18 words.
- cost must be an object with exactly raw and label.
- cost.raw must be a number in TRIP_PARAMETERS.currency.
- cost.label and total.label must include TRIP_PARAMETERS.currency or its symbol.
- total.raw must equal the sum of that day's item cost.raw values.

APP_JS_JSON_FORMAT:
Use this exact shape because the frontend app.js renders these fields directly.
Replace all example values with real itinerary values for TRIP_PARAMETERS.
Repeat the schedule day object until schedule.length equals TRIP_PARAMETERS.days.
Each day.items array must contain exactly 4 activity objects.
Do not copy placeholder text.
{{
  "destination": "Destination name from TRIP_PARAMETERS",
  "country": "Destination country",
  "summary": "Short trip overview under 25 words.",
  "transport": "One plain-text transport paragraph under 45 words.",
  "food": [
    "Local food recommendation 1",
    "Local food recommendation 2",
    "Local food recommendation 3"
  ],
  "breakdown": [
    {{"label": "Accommodation", "percent": 35, "amount": 0}},
    {{"label": "Food", "percent": 20, "amount": 0}},
    {{"label": "Transportation", "percent": 15, "amount": 0}},
    {{"label": "Activities", "percent": 20, "amount": 0}},
    {{"label": "Buffer", "percent": 10, "amount": 0}}
  ],
  "schedule": [
    {{
      "day": 1,
      "title": "Unique day theme",
      "items": [
        {{"time": "08:30", "title": "Breakfast or arrival activity", "notes": "Describe what the traveler does in this activity.", "cost": {{"raw": 0, "label": "MYR0"}}}},
        {{"time": "10:30", "title": "Morning activity at a real place", "notes": "Describe what the traveler does in this activity.", "cost": {{"raw": 0, "label": "MYR0"}}}},
        {{"time": "14:00", "title": "Afternoon activity at a real place", "notes": "Describe what the traveler does in this activity.", "cost": {{"raw": 0, "label": "MYR0"}}}},
        {{"time": "19:30", "title": "Evening meal or nightlife activity", "notes": "Describe what the traveler does in this activity.", "cost": {{"raw": 0, "label": "MYR0"}}}}
      ],
      "total": {{"raw": 0, "label": "MYR0"}}
    }}
  ]
}}

QUALITY_RULES:
- Create varied activities across days. Do not repeat activity titles.
- Route nearby places together in the same day.
- Include requested places when realistic: TRIP_PARAMETERS.placesUserWants.
- Match budgetStyle: Student/Backpacker cheap, Comfort balanced, Luxury premium.
- Use cost.raw 0 only for genuinely free activities.
- Do not output empty arrays.
- Do not output markdown, comments, explanations, or text before/after JSON.

FORBIDDEN_OUTPUT:
- Do not return breakdown as an object.
- Do not return transport as an object.
- Do not use keys like "cost.raw" or "cost.label".
- Do not return only one day unless TRIP_PARAMETERS.days is 1.
- Do not repeat the same day title or activity title.

FINAL_SELF_CHECK:
- Does schedule.length equal TRIP_PARAMETERS.days?
- Does every day have exactly 4 items?
- Does every item have time, title, notes, and nested cost?
- Is breakdown an array of exactly 5 objects?
- Is the final answer valid JSON only?
""".strip()

    def upsert_user(self, userinfo):
        timestamp = now()
        with connect_db() as conn:
            existing = conn.execute(
                f"SELECT id FROM users WHERE email = {SQL_PARAM} OR google_user_id = {SQL_PARAM}",
                (userinfo["email"], userinfo["sub"]),
            ).fetchone()
            if existing:
                conn.execute(
                    f"""
                    UPDATE users
                    SET google_user_id = {SQL_PARAM}, full_name = {SQL_PARAM}, email = {SQL_PARAM}, profile_picture = {SQL_PARAM}, updated_at = {SQL_PARAM}
                    WHERE id = {SQL_PARAM}
                    """,
                    (
                        userinfo["sub"],
                        userinfo.get("name") or userinfo["email"],
                        userinfo["email"],
                        userinfo.get("picture"),
                        timestamp,
                        existing["id"],
                    ),
                )
                return existing["id"]

            if USE_POSTGRES:
                row = conn.execute(
                    """
                    INSERT INTO users (google_user_id, full_name, email, profile_picture, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        userinfo["sub"],
                        userinfo.get("name") or userinfo["email"],
                        userinfo["email"],
                        userinfo.get("picture"),
                        timestamp,
                        timestamp,
                    ),
                ).fetchone()
                return row["id"]

            cursor = conn.execute(
                """
                INSERT INTO users (google_user_id, full_name, email, profile_picture, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    userinfo["sub"],
                    userinfo.get("name") or userinfo["email"],
                    userinfo["email"],
                    userinfo.get("picture"),
                    timestamp,
                    timestamp,
                ),
            )
            return cursor.lastrowid

    def create_session(self, user_id):
        session_token = secrets.token_urlsafe(48)
        timestamp = now()
        with connect_db() as conn:
            conn.execute(
                f"INSERT INTO sessions (token_hash, user_id, expires_at, created_at) VALUES ({SQL_PARAM}, {SQL_PARAM}, {SQL_PARAM}, {SQL_PARAM})",
                (
                    token_hash(session_token),
                    user_id,
                    timestamp + SESSION_DAYS * 24 * 60 * 60,
                    timestamp,
                ),
            )
            conn.execute(f"DELETE FROM sessions WHERE expires_at <= {SQL_PARAM}", (timestamp,))
        return session_token

    def handle_logout(self):
        token = self.read_cookies().get("tg_session")
        if token:
            with connect_db() as conn:
                conn.execute(f"DELETE FROM sessions WHERE token_hash = {SQL_PARAM}", (token_hash(token),))
        self.send_json(
            {"ok": True},
            extra_headers=[("Set-Cookie", cookie_header("tg_session", "", 0))],
        )


def main():
    init_db()
    os.chdir(ROOT)
    httpd = ThreadingHTTPServer((HOST, PORT), TravelGenieHandler)
    print(f"TravelGenie running at http://{HOST}:{PORT}/")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
