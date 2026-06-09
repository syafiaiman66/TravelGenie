import hashlib
import hmac
import json
import os
import secrets
import smtplib
import ssl
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from email.message import EmailMessage
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
DATA_ENCRYPTION_SECRET = os.environ.get("DATA_ENCRYPTION_SECRET", "")


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
FEEDBACK_TO = os.environ.get("FEEDBACK_TO") or "bouncebtoe@gmail.com"
SMTP_HOST = os.environ.get("SMTP_HOST") or ""
SMTP_PORT = int(os.environ.get("SMTP_PORT") or "587")
SMTP_USERNAME = os.environ.get("SMTP_USERNAME") or ""
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD") or ""
SMTP_FROM = os.environ.get("SMTP_FROM") or SMTP_USERNAME or FEEDBACK_TO


def connect_db():
    if USE_POSTGRES:
        return psycopg.connect(DATABASE_URL, row_factory=dict_row)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_table_columns(conn, table):
    if USE_POSTGRES:
        rows = conn.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = current_schema() AND table_name = %s
            """,
            (table,),
        ).fetchall()
        return {row["column_name"] for row in rows}

    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {row["name"] for row in rows}


def ensure_column(conn, table, column, definition):
    if column not in get_table_columns(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db():
    user_id_column = "SERIAL PRIMARY KEY" if USE_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"
    with connect_db() as conn:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS users (
                id {user_id_column},
                google_user_id TEXT UNIQUE,
                full_name TEXT NOT NULL,
                email_encrypted TEXT,
                profile_picture TEXT,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            )
            """
        )
        ensure_column(conn, "users", "google_user_id", "TEXT")
        ensure_column(conn, "users", "full_name", "TEXT")
        ensure_column(conn, "users", "email_encrypted", "TEXT")
        ensure_column(conn, "users", "profile_picture", "TEXT")
        ensure_column(conn, "users", "created_at", "INTEGER")
        ensure_column(conn, "users", "updated_at", "INTEGER")
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_user_id ON users (google_user_id) WHERE google_user_id IS NOT NULL"
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

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS itineraries (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                tripname_encrypted TEXT NOT NULL,
                destination_encrypted TEXT NOT NULL,
                currency TEXT NOT NULL,
                budget REAL NOT NULL,
                days INTEGER NOT NULL,
                travelers INTEGER NOT NULL,
                itinerary_json TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
            """
        )
        ensure_column(conn, "itineraries", "tripname_encrypted", "TEXT")
        ensure_column(conn, "itineraries", "destination_encrypted", "TEXT")
        ensure_column(conn, "itineraries", "currency", "TEXT")
        ensure_column(conn, "itineraries", "budget", "REAL")
        ensure_column(conn, "itineraries", "days", "INTEGER")
        ensure_column(conn, "itineraries", "travelers", "INTEGER")
        ensure_column(conn, "itineraries", "itinerary_json", "TEXT")
        ensure_column(conn, "itineraries", "created_at", "INTEGER")
        ensure_column(conn, "itineraries", "updated_at", "INTEGER")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_itineraries_user_id ON itineraries (user_id)")
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

def protect_value(value, normalize=False):
    text = str(value or "").strip()
    if normalize:
        text = text.lower()
    if not text:
        return ""

    secret = DATA_ENCRYPTION_SECRET.strip()
    if secret:
        return hmac.new(secret.encode("utf-8"), text.encode("utf-8"), hashlib.sha256).hexdigest()
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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
    return detail[:280] if detail else "AI did not return an error message."


class BounceHandler(SimpleHTTPRequestHandler):
    server_version = "Bounce/1.0"

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
        if parsed.path == "/api/itineraries":
            self.handle_list_itineraries()
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
        if parsed.path == "/api/itineraries":
            self.handle_save_itinerary()
            return
        if parsed.path == "/api/feedback":
            self.handle_feedback()
            return
        if parsed.path == "/auth/logout":
            self.handle_logout()
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/api/itineraries/"):
            self.handle_update_itinerary(parsed)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.startswith("/api/itineraries/"):
            self.handle_delete_itinerary(parsed)
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
            columns = get_table_columns(conn, "users")
            email_select = "users.email" if "email" in columns else "NULL"
            encrypted_select = "users.email_encrypted" if "email_encrypted" in columns else "NULL"
            row = conn.execute(
                f"""
                SELECT users.id, users.google_user_id, users.full_name,
                       {email_select} AS email,
                       {encrypted_select} AS email_encrypted,
                       users.profile_picture
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
                    "email": user.get("email") or "",
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
            self.send_json({"error": "missing_ai_config"}, HTTPStatus.SERVICE_UNAVAILABLE)
            return

        try:
            trip_request = self.read_json_body()
            itinerary = self.generate_itinerary_with_gemini(trip_request, api_key)
        except ValueError as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        except GeminiGenerationError as exc:
            self.send_json({"error": "ai_generation_failed", "detail": str(exc)}, HTTPStatus.BAD_GATEWAY)
            return
        except Exception as exc:
            print(f"AI generation error: {exc!r}", file=sys.stderr, flush=True)
            self.send_json(
                {"error": "ai_generation_failed", "detail": "The server could not read the AI response."},
                HTTPStatus.BAD_GATEWAY,
            )
            return

        self.send_json({"itinerary": itinerary})

    def parse_itinerary_id(self, parsed):
        parts = parsed.path.strip("/").split("/")
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "itineraries" and parts[2]:
            return urllib.parse.unquote(parts[2])
        return ""

    def itinerary_row_to_trip(self, row):
        data = dict(row)
        try:
            trip = json.loads(data["itinerary_json"])
            if not isinstance(trip, dict):
                trip = {}
        except (TypeError, json.JSONDecodeError):
            trip = {}

        trip["id"] = data["id"]
        trip["name"] = trip.get("name") or data.get("trip_name") or "Saved Trip"
        trip["destination"] = trip.get("destination") or data.get("destination") or "Saved Destination"
        trip["currency"] = trip.get("currency") or data.get("currency") or "USD"
        trip["budget"] = trip.get("budget") or data.get("budget") or 0
        trip["days"] = trip.get("days") or data.get("days") or 1
        trip["travelers"] = trip.get("travelers") or data.get("travelers") or 1
        trip["createdAt"] = trip.get("createdAt") or data.get("created_at")
        trip["updatedAt"] = data.get("updated_at")
        return trip

    def itinerary_text_fields(self, columns, trip_name, destination):
        has_encrypted_name = "tripname_encrypted" in columns or "trip_name_encrypted" in columns
        has_encrypted_destination = "destination_encrypted" in columns
        protected_name = protect_value(trip_name)
        protected_destination = protect_value(destination)
        fields = {}

        if "tripname_encrypted" in columns:
            fields["tripname_encrypted"] = protected_name
        if "trip_name_encrypted" in columns:
            fields["trip_name_encrypted"] = protected_name
        if "destination_encrypted" in columns:
            fields["destination_encrypted"] = protected_destination
        if "trip_name" in columns:
            fields["trip_name"] = protected_name if has_encrypted_name else trip_name
        if "destination" in columns:
            fields["destination"] = protected_destination if has_encrypted_destination else destination

        return fields

    def normalize_itinerary_payload(self, payload, forced_id=None):
        if not isinstance(payload, dict):
            raise ValueError("invalid_itinerary")

        trip = dict(payload)
        trip_id = str(forced_id or trip.get("id") or secrets.token_urlsafe(18)).strip()
        name = str(trip.get("name") or trip.get("tripName") or "Untitled Trip").strip()[:180]
        destination = str(trip.get("destination") or "").strip()[:180]
        currency = str(trip.get("currency") or "").strip()[:12]

        try:
            budget = float(trip.get("budget") or 0)
            days = int(trip.get("days") or 0)
            travelers = int(trip.get("travelers") or 0)
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid_itinerary") from exc

        if not trip_id or len(trip_id) > 120 or not destination or not currency or days <= 0 or travelers <= 0:
            raise ValueError("invalid_itinerary")
        if not isinstance(trip.get("schedule"), list):
            raise ValueError("invalid_itinerary")

        trip.update(
            {
                "id": trip_id,
                "name": name,
                "destination": destination,
                "currency": currency,
                "budget": budget,
                "days": days,
                "travelers": travelers,
            }
        )

        return {
            "id": trip_id,
            "trip_name": name,
            "destination": destination,
            "currency": currency,
            "budget": budget,
            "days": days,
            "travelers": travelers,
            "trip": trip,
        }

    def save_itinerary_payload(self, payload, user_id, forced_id=None, require_existing=False):
        record = self.normalize_itinerary_payload(payload, forced_id)
        timestamp = now()

        with connect_db() as conn:
            columns = get_table_columns(conn, "itineraries")
            existing = conn.execute(
                f"SELECT user_id, created_at FROM itineraries WHERE id = {SQL_PARAM}",
                (record["id"],),
            ).fetchone()

            if require_existing and not existing:
                raise LookupError("itinerary_not_found")
            if existing and existing["user_id"] != user_id:
                raise PermissionError("forbidden")

            created_at = existing["created_at"] if existing else timestamp
            trip = record["trip"]
            trip["createdAt"] = trip.get("createdAt") or created_at
            trip["updatedAt"] = timestamp
            itinerary_json = json.dumps(trip, ensure_ascii=False, separators=(",", ":"))
            text_fields = self.itinerary_text_fields(columns, record["trip_name"], record["destination"])

            base_fields = {
                "user_id": user_id,
                "currency": record["currency"],
                "budget": record["budget"],
                "days": record["days"],
                "travelers": record["travelers"],
                "itinerary_json": itinerary_json,
                "updated_at": timestamp,
                **text_fields,
            }

            if existing:
                update_fields = {key: value for key, value in base_fields.items() if key != "user_id" and key in columns}
                assignments = ", ".join(f"{key} = {SQL_PARAM}" for key in update_fields)
                conn.execute(
                    f"UPDATE itineraries SET {assignments} WHERE id = {SQL_PARAM} AND user_id = {SQL_PARAM}",
                    (*update_fields.values(), record["id"], user_id),
                )
            else:
                insert_fields = {
                    "id": record["id"],
                    **{key: value for key, value in base_fields.items() if key in columns or key == "user_id"},
                    "created_at": created_at,
                }
                field_names = list(insert_fields.keys())
                placeholders = ", ".join([SQL_PARAM] * len(field_names))
                conn.execute(
                    f"INSERT INTO itineraries ({', '.join(field_names)}) VALUES ({placeholders})",
                    tuple(insert_fields.values()),
                )

        return trip

    def handle_list_itineraries(self):
        user = self.get_session_user()
        if not user:
            self.send_json({"error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
            return

        with connect_db() as conn:
            rows = conn.execute(
                f"""
                SELECT *
                FROM itineraries
                WHERE user_id = {SQL_PARAM}
                ORDER BY updated_at DESC, created_at DESC
                """,
                (user["id"],),
            ).fetchall()

        self.send_json({"trips": [self.itinerary_row_to_trip(row) for row in rows]})

    def handle_save_itinerary(self):
        user = self.get_session_user()
        if not user:
            self.send_json({"error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
            return

        try:
            payload = self.read_json_body()
            trip = self.save_itinerary_payload(payload, user["id"])
        except json.JSONDecodeError:
            self.send_json({"error": "invalid_json"}, HTTPStatus.BAD_REQUEST)
            return
        except ValueError as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        except PermissionError as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.FORBIDDEN)
            return

        self.send_json({"trip": trip})

    def handle_update_itinerary(self, parsed):
        trip_id = self.parse_itinerary_id(parsed)
        if not trip_id:
            self.send_json({"error": "itinerary_not_found"}, HTTPStatus.NOT_FOUND)
            return

        user = self.get_session_user()
        if not user:
            self.send_json({"error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
            return

        try:
            payload = self.read_json_body()
            trip = self.save_itinerary_payload(payload, user["id"], forced_id=trip_id, require_existing=True)
        except json.JSONDecodeError:
            self.send_json({"error": "invalid_json"}, HTTPStatus.BAD_REQUEST)
            return
        except ValueError as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            return
        except LookupError as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.NOT_FOUND)
            return
        except PermissionError as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.FORBIDDEN)
            return

        self.send_json({"trip": trip})

    def handle_delete_itinerary(self, parsed):
        trip_id = self.parse_itinerary_id(parsed)
        if not trip_id:
            self.send_json({"error": "itinerary_not_found"}, HTTPStatus.NOT_FOUND)
            return

        user = self.get_session_user()
        if not user:
            self.send_json({"error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
            return

        with connect_db() as conn:
            existing = conn.execute(
                f"SELECT user_id FROM itineraries WHERE id = {SQL_PARAM}",
                (trip_id,),
            ).fetchone()
            if not existing:
                self.send_json({"error": "itinerary_not_found"}, HTTPStatus.NOT_FOUND)
                return
            if existing["user_id"] != user["id"]:
                self.send_json({"error": "forbidden"}, HTTPStatus.FORBIDDEN)
                return
            conn.execute(
                f"DELETE FROM itineraries WHERE id = {SQL_PARAM} AND user_id = {SQL_PARAM}",
                (trip_id, user["id"]),
            )

        self.send_json({"ok": True})
    def handle_feedback(self):
        user = self.get_session_user()
        if not user:
            self.send_json({"error": "unauthorized"}, HTTPStatus.UNAUTHORIZED)
            return

        try:
            payload = self.read_json_body()
            message = str(payload.get("message") or "").strip()
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.send_json({"error": "invalid_json"}, HTTPStatus.BAD_REQUEST)
            return

        if len(message) < 5:
            self.send_json({"error": "feedback_too_short"}, HTTPStatus.BAD_REQUEST)
            return
        if len(message) > 4000:
            self.send_json({"error": "feedback_too_long"}, HTTPStatus.BAD_REQUEST)
            return

        try:
            self.send_feedback_email(message, user)
        except RuntimeError as exc:
            self.send_json({"error": str(exc)}, HTTPStatus.SERVICE_UNAVAILABLE)
            return
        except smtplib.SMTPAuthenticationError as exc:
            print(f"Feedback SMTP authentication failed: {exc.smtp_code} {exc.smtp_error!r}", file=sys.stderr, flush=True)
            self.send_json({"error": "feedback_smtp_auth_failed"}, HTTPStatus.BAD_GATEWAY)
            return
        except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected, TimeoutError, OSError) as exc:
            print(f"Feedback SMTP connection failed: {exc!r}", file=sys.stderr, flush=True)
            self.send_json({"error": "feedback_smtp_connection_failed"}, HTTPStatus.BAD_GATEWAY)
            return
        except smtplib.SMTPException as exc:
            print(f"Feedback SMTP failed: {exc!r}", file=sys.stderr, flush=True)
            self.send_json({"error": "feedback_smtp_failed"}, HTTPStatus.BAD_GATEWAY)
            return
        except Exception as exc:
            print(f"Feedback email failed: {exc!r}", file=sys.stderr, flush=True)
            self.send_json({"error": "feedback_send_failed"}, HTTPStatus.BAD_GATEWAY)
            return

        self.send_json({"ok": True})

    def send_feedback_email(self, message, user):
        if not SMTP_HOST or not SMTP_FROM or not FEEDBACK_TO:
            raise RuntimeError("missing_feedback_email_config")

        sender_name = user.get("full_name") if user else "Anonymous visitor"
        sender_email = user.get("email") if user else ""
        email = EmailMessage()
        email["Subject"] = "Bounce customer feedback"
        email["From"] = SMTP_FROM
        email["To"] = FEEDBACK_TO
        if sender_email:
            email["Reply-To"] = sender_email
        email.set_content(
            "\n".join(
                [
                    "New Bounce feedback was submitted.",
                    "",
                    f"Name: {sender_name or 'Unknown'}",
                    f"Email: {sender_email or 'Not signed in'}",
                    f"Submitted at: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}",
                    "",
                    "Message:",
                    message,
                ]
            )
        )

        if SMTP_PORT == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=15) as smtp:
                if SMTP_USERNAME or SMTP_PASSWORD:
                    smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
                smtp.send_message(email)
            return

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            if SMTP_USERNAME or SMTP_PASSWORD:
                smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
            smtp.send_message(email)

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
        print(f"AI request started for {GEMINI_MODEL}", file=sys.stderr, flush=True)
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
                print(f"AI request finished in {elapsed:.1f}s", file=sys.stderr, flush=True)
                return payload
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            summary = json_error_summary(detail)
            print(f"AI API HTTP error {exc.code}: {detail}", file=sys.stderr, flush=True)
            raise GeminiGenerationError(f"AI API error {exc.code}: {summary}") from exc
        except urllib.error.URLError as exc:
            print(f"AI network error: {exc!r}", file=sys.stderr, flush=True)
            raise GeminiGenerationError(f"Could not reach the AI service: {exc.reason}") from exc

    def parse_gemini_itinerary(self, gemini_payload):
        prompt_feedback = gemini_payload.get("promptFeedback") or {}
        if prompt_feedback.get("blockReason"):
            raise GeminiGenerationError(f"AI blocked the prompt: {prompt_feedback['blockReason']}.")

        candidate = (gemini_payload.get("candidates") or [{}])[0]
        content = candidate.get("content") or {}
        parts = content.get("parts") or []
        text = "".join(part.get("text", "") for part in parts).strip()
        if not text:
            finish_reason = candidate.get("finishReason", "unknown")
            raise GeminiGenerationError(f"AI returned no itinerary text. Finish reason: {finish_reason}.")

        try:
            return parse_itinerary_json(text)
        except json.JSONDecodeError as exc:
            print(f"AI returned non-JSON text: {text[:1000]}", file=sys.stderr, flush=True)
            raise GeminiGenerationError("AI returned text that was not valid itinerary JSON.") from exc

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

        currency = str(trip_request["currency"]).strip().upper()
        prompt_payload = {
            "destination": destination,
            "totalBudget": budget,
            "currency": currency,
            "budgetCurrency": currency,
            "travelers": travelers,
            "people": travelers,
            "days": min(days, 21),
            "tripName": str(trip_request.get("tripName") or "").strip(),
            "interests": trip_request.get("interests") or [],
            "placesUserWants": trip_request.get("customPlaces") or [],
            "budgetStyle": str(trip_request["budgetStyle"]).strip(),
        }

        return f"""
You are Bounce. Generate one complete travel itinerary that matches the provided JSON schema.

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

CURRENCY_RULES:
- Use the user-selected currency as the budget currency.
- Keep all estimated costs in that currency.
- Do not convert to another currency unless the user asks.
- The selected currency is TRIP_PARAMETERS.currency.
- Reason about practical costs using that selected currency and the user's totalBudget.
- breakdown.amount, cost.raw, and total.raw must all be numeric amounts in TRIP_PARAMETERS.currency.

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
        {{"time": "08:30", "title": "Breakfast or arrival activity", "notes": "Describe what the traveler does in this activity.", "cost": {{"raw": 0, "label": "{currency} 0"}}}},
        {{"time": "10:30", "title": "Morning activity at a real place", "notes": "Describe what the traveler does in this activity.", "cost": {{"raw": 0, "label": "{currency} 0"}}}},
        {{"time": "14:00", "title": "Afternoon activity at a real place", "notes": "Describe what the traveler does in this activity.", "cost": {{"raw": 0, "label": "{currency} 0"}}}},
        {{"time": "19:30", "title": "Evening meal or nightlife activity", "notes": "Describe what the traveler does in this activity.", "cost": {{"raw": 0, "label": "{currency} 0"}}}}
      ],
      "total": {{"raw": 0, "label": "{currency} 0"}}
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
        email = userinfo["email"].strip().lower()
        full_name = userinfo.get("name") or email
        email_protected = protect_value(email, normalize=True)

        with connect_db() as conn:
            columns = get_table_columns(conn, "users")
            if "email" in columns:
                existing = conn.execute(
                    f"SELECT id FROM users WHERE google_user_id = {SQL_PARAM} OR email = {SQL_PARAM}",
                    (userinfo["sub"], email),
                ).fetchone()
            else:
                existing = conn.execute(
                    f"SELECT id FROM users WHERE google_user_id = {SQL_PARAM}",
                    (userinfo["sub"],),
                ).fetchone()

            if existing:
                updates = {
                    "google_user_id": userinfo["sub"],
                    "full_name": full_name,
                    "profile_picture": userinfo.get("picture"),
                    "updated_at": timestamp,
                }
                if "email_encrypted" in columns:
                    updates["email_encrypted"] = email_protected
                if "email" in columns:
                    updates["email"] = email

                assignments = ", ".join(f"{key} = {SQL_PARAM}" for key in updates)
                conn.execute(
                    f"UPDATE users SET {assignments} WHERE id = {SQL_PARAM}",
                    (*updates.values(), existing["id"]),
                )
                return existing["id"]

            insert_fields = {
                "google_user_id": userinfo["sub"],
                "full_name": full_name,
                "profile_picture": userinfo.get("picture"),
                "created_at": timestamp,
                "updated_at": timestamp,
            }
            if "email_encrypted" in columns:
                insert_fields["email_encrypted"] = email_protected
            if "email" in columns:
                insert_fields["email"] = email

            field_names = list(insert_fields.keys())
            placeholders = ", ".join([SQL_PARAM] * len(field_names))
            if USE_POSTGRES:
                row = conn.execute(
                    f"INSERT INTO users ({', '.join(field_names)}) VALUES ({placeholders}) RETURNING id",
                    tuple(insert_fields.values()),
                ).fetchone()
                return row["id"]

            cursor = conn.execute(
                f"INSERT INTO users ({', '.join(field_names)}) VALUES ({placeholders})",
                tuple(insert_fields.values()),
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
    httpd = ThreadingHTTPServer((HOST, PORT), BounceHandler)
    print(f"Bounce running at http://{HOST}:{PORT}/")
    httpd.serve_forever()


if __name__ == "__main__":
    main()

