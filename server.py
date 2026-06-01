import hashlib
import json
import os
import secrets
import sqlite3
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
