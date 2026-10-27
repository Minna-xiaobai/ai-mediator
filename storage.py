"""Account, room, summary, and report storage.

Uses PostgreSQL when a database URL is configured (cloud deployment) and a
local SQLite file otherwise. Queries are written once with ``?`` placeholders
and translated for PostgreSQL by ``_PostgresConnection``.
"""

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

DATABASE_PATH = Path(
    os.getenv(
        "MEDIATOR_DB_PATH",
        str(Path(__file__).resolve().with_name("mediator.sqlite3")),
    )
).resolve()
INVITE_TTL_SECONDS = 24 * 60 * 60
MAX_SUMMARY_LENGTH = 4000
_USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,32}$")
_INVITE_ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
# Serialises PostgreSQL transactions that SQLite runs under BEGIN IMMEDIATE.
_PG_LOCK_KEY = 73_100_001

_database_url = os.getenv("DATABASE_URL", "").strip()
_pg_pool = None


class StorageError(Exception):
    """Raised when an account, invite, or room operation is invalid.

    ``code`` is a translation key (see i18n.py); ``params`` fill its placeholders.
    """

    def __init__(self, code: str, **params: Any) -> None:
        super().__init__(code)
        self.code = code
        self.params = params


def configure(database_url: str) -> None:
    """Use PostgreSQL at database_url for calls that do not pass a db_path."""
    global _database_url, _pg_pool
    database_url = database_url.strip()
    if database_url != _database_url and _pg_pool is not None:
        _pg_pool.close()
        _pg_pool = None
    _database_url = database_url


def using_postgres() -> bool:
    return bool(_database_url)


class _ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


class _PostgresConnection:
    """Gives a pooled psycopg connection the small sqlite3-style API used here."""

    def __init__(self, pool) -> None:
        self._pool_context = pool.connection()
        self._connection = None

    def __enter__(self) -> "_PostgresConnection":
        self._connection = self._pool_context.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return self._pool_context.__exit__(exc_type, exc_value, traceback)

    def execute(self, sql: str, params: tuple = ()):
        if sql.strip() == "BEGIN IMMEDIATE":
            return self._connection.execute(
                "SELECT pg_advisory_xact_lock(%s)", (_PG_LOCK_KEY,)
            )
        return self._connection.execute(sql.replace("?", "%s"), params)

    def executescript(self, script: str) -> None:
        for statement in script.split(";"):
            if statement.strip():
                self._connection.execute(statement)


def _postgres_pool():
    global _pg_pool
    if _pg_pool is None:
        from psycopg.rows import dict_row
        from psycopg_pool import ConnectionPool

        # prepare_threshold=None keeps this compatible with transaction-mode
        # poolers such as Supabase's, which do not support prepared statements.
        _pg_pool = ConnectionPool(
            _database_url,
            min_size=1,
            max_size=5,
            kwargs={"row_factory": dict_row, "prepare_threshold": None},
            open=True,
        )
    return _pg_pool


def _integrity_errors() -> tuple[type[Exception], ...]:
    if not using_postgres():
        return (sqlite3.IntegrityError,)
    import psycopg

    return (sqlite3.IntegrityError, psycopg.IntegrityError)


def _connect(db_path: str | Path | None = None):
    if db_path is None and using_postgres():
        return _PostgresConnection(_postgres_pool())
    path = Path(db_path) if db_path is not None else DATABASE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10, factory=_ClosingConnection)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


_SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_salt TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS rooms (
    room_id TEXT PRIMARY KEY,
    invite_hash TEXT NOT NULL UNIQUE,
    invite_expires_at INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('waiting', 'paired')),
    created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS memberships (
    room_id TEXT NOT NULL REFERENCES rooms(room_id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('A', 'B')),
    joined_at INTEGER NOT NULL,
    PRIMARY KEY (room_id, user_id),
    UNIQUE (room_id, role)
);
CREATE TABLE IF NOT EXISTS summaries (
    room_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    content TEXT NOT NULL,
    consent INTEGER NOT NULL CHECK (consent IN (0, 1)),
    updated_at INTEGER NOT NULL,
    PRIMARY KEY (room_id, user_id),
    FOREIGN KEY (room_id, user_id)
        REFERENCES memberships(room_id, user_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS reports (
    room_id TEXT PRIMARY KEY REFERENCES rooms(room_id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS report_generation (
    room_id TEXT PRIMARY KEY REFERENCES rooms(room_id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    lease_expires_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS memberships_user_idx
    ON memberships(user_id, room_id);
"""

# Row level security is enabled with no policies so that hosted Postgres
# providers' public REST APIs (e.g. Supabase) cannot read these tables; the
# table owner used by this app bypasses RLS.
_POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    password_salt TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at BIGINT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS users_username_lower_idx ON users (lower(username));
CREATE TABLE IF NOT EXISTS rooms (
    room_id TEXT PRIMARY KEY,
    invite_hash TEXT NOT NULL UNIQUE,
    invite_expires_at BIGINT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('waiting', 'paired')),
    created_at BIGINT NOT NULL
);
CREATE TABLE IF NOT EXISTS memberships (
    room_id TEXT NOT NULL REFERENCES rooms(room_id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('A', 'B')),
    joined_at BIGINT NOT NULL,
    PRIMARY KEY (room_id, user_id),
    UNIQUE (room_id, role)
);
CREATE TABLE IF NOT EXISTS summaries (
    room_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    content TEXT NOT NULL,
    consent INTEGER NOT NULL CHECK (consent IN (0, 1)),
    updated_at BIGINT NOT NULL,
    PRIMARY KEY (room_id, user_id),
    FOREIGN KEY (room_id, user_id)
        REFERENCES memberships(room_id, user_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS reports (
    room_id TEXT PRIMARY KEY REFERENCES rooms(room_id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at BIGINT NOT NULL
);
CREATE TABLE IF NOT EXISTS report_generation (
    room_id TEXT PRIMARY KEY REFERENCES rooms(room_id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    lease_expires_at BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS memberships_user_idx ON memberships(user_id, room_id);
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE rooms ENABLE ROW LEVEL SECURITY;
ALTER TABLE memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE report_generation ENABLE ROW LEVEL SECURITY
"""


def initialize_storage(db_path: str | Path | None = None) -> None:
    postgres = db_path is None and using_postgres()
    with _connect(db_path) as connection:
        if postgres:
            connection.execute("BEGIN IMMEDIATE")
        connection.executescript(_POSTGRES_SCHEMA if postgres else _SQLITE_SCHEMA)


REPORT_GENERATION_LEASE_SECONDS = 300


def get_report_generation_state(
    user_id: str,
    room_id: str,
    db_path: str | Path | None = None,
) -> str:
    now = int(time.time())
    with _connect(db_path) as connection:
        membership = connection.execute(
            "SELECT 1 FROM memberships WHERE room_id = ? AND user_id = ?",
            (room_id, user_id),
        ).fetchone()
        if membership is None:
            raise StorageError("err_room_not_found")
        report = connection.execute(
            "SELECT 1 FROM reports WHERE room_id = ?", (room_id,)
        ).fetchone()
        if report is not None:
            return "completed"
        generation = connection.execute(
            "SELECT lease_expires_at FROM report_generation WHERE room_id = ?",
            (room_id,),
        ).fetchone()
    if generation is not None and generation["lease_expires_at"] > now:
        return "generating"
    return "ready"


def claim_report_generation(
    user_id: str,
    room_id: str,
    db_path: str | Path | None = None,
) -> str:
    now = int(time.time())
    with _connect(db_path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        membership = connection.execute(
            "SELECT 1 FROM memberships WHERE room_id = ? AND user_id = ?",
            (room_id, user_id),
        ).fetchone()
        if membership is None:
            raise StorageError("err_room_not_found")

        report = connection.execute(
            "SELECT 1 FROM reports WHERE room_id = ?", (room_id,)
        ).fetchone()
        if report is not None:
            return "completed"

        member_count = connection.execute(
            "SELECT COUNT(*) AS n FROM memberships WHERE room_id = ?", (room_id,)
        ).fetchone()["n"]
        consent_count = connection.execute(
            """
            SELECT COUNT(*) AS n FROM memberships AS m
            JOIN summaries AS s
              ON s.room_id = m.room_id AND s.user_id = m.user_id
            WHERE m.room_id = ? AND s.consent = 1
            """,
            (room_id,),
        ).fetchone()["n"]
        if member_count != 2 or consent_count != 2:
            raise StorageError("err_consent_required")

        cursor = connection.execute(
            """
            INSERT INTO report_generation (room_id, user_id, lease_expires_at)
            VALUES (?, ?, ?)
            ON CONFLICT(room_id) DO UPDATE SET
                user_id = excluded.user_id,
                lease_expires_at = excluded.lease_expires_at
            WHERE report_generation.lease_expires_at <= ?
            """,
            (room_id, user_id, now + REPORT_GENERATION_LEASE_SECONDS, now),
        )
        if cursor.rowcount == 1:
            return "claimed"
        return "generating"


def release_report_generation(
    user_id: str,
    room_id: str,
    db_path: str | Path | None = None,
) -> None:
    with _connect(db_path) as connection:
        connection.execute(
            "DELETE FROM report_generation WHERE room_id = ? AND user_id = ?",
            (room_id, user_id),
        )


def _password_hash(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)


def register_user(
    username: str,
    password: str,
    db_path: str | Path | None = None,
) -> dict[str, str]:
    normalized_username = username.strip()
    if not _USERNAME_PATTERN.fullmatch(normalized_username):
        raise StorageError("err_username_format")
    if not 12 <= len(password) <= 128:
        raise StorageError("err_password_length")

    salt = secrets.token_bytes(16)
    user = {
        "user_id": uuid.uuid4().hex,
        "username": normalized_username,
        "password_salt": salt.hex(),
        "password_hash": _password_hash(password, salt).hex(),
        "created_at": str(int(time.time())),
    }
    try:
        with _connect(db_path) as connection:
            connection.execute(
                """
                INSERT INTO users (user_id, username, password_salt, password_hash, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user["user_id"],
                    user["username"],
                    user["password_salt"],
                    user["password_hash"],
                    int(user["created_at"]),
                ),
            )
    except _integrity_errors() as error:
        raise StorageError("err_username_taken") from error
    return {"user_id": user["user_id"], "username": user["username"]}


def authenticate_user(
    username: str,
    password: str,
    db_path: str | Path | None = None,
) -> dict[str, str] | None:
    with _connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT user_id, username, password_salt, password_hash
            FROM users WHERE lower(username) = lower(?)
            """,
            (username.strip(),),
        ).fetchone()
    if row is None:
        return None

    candidate_hash = _password_hash(password, bytes.fromhex(row["password_salt"]))
    if not hmac.compare_digest(candidate_hash.hex(), row["password_hash"]):
        return None
    return {"user_id": row["user_id"], "username": row["username"]}


def delete_user(
    user_id: str,
    password: str,
    db_path: str | Path | None = None,
) -> None:
    """Delete an account and every room it belongs to, after re-checking the password."""
    with _connect(db_path) as connection:
        row = connection.execute(
            "SELECT password_salt, password_hash FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if row is None or not hmac.compare_digest(
            _password_hash(password, bytes.fromhex(row["password_salt"])).hex(),
            row["password_hash"],
        ):
            raise StorageError("err_wrong_password")
        connection.execute(
            """
            DELETE FROM rooms WHERE room_id IN (
                SELECT room_id FROM memberships WHERE user_id = ?
            )
            """,
            (user_id,),
        )
        connection.execute("DELETE FROM users WHERE user_id = ?", (user_id,))


def create_room(
    user_id: str,
    db_path: str | Path | None = None,
) -> tuple[str, str]:
    room_id = uuid.uuid4().hex
    invite_code = "".join(secrets.choice(_INVITE_ALPHABET) for _ in range(10))
    invite_hash = hashlib.sha256(invite_code.encode("ascii")).hexdigest()
    now = int(time.time())
    with _connect(db_path) as connection:
        user_exists = connection.execute(
            "SELECT 1 FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        if user_exists is None:
            raise StorageError("err_relogin")
        connection.execute(
            """
            INSERT INTO rooms (room_id, invite_hash, invite_expires_at, status, created_at)
            VALUES (?, ?, ?, 'waiting', ?)
            """,
            (room_id, invite_hash, now + INVITE_TTL_SECONDS, now),
        )
        connection.execute(
            """
            INSERT INTO memberships (room_id, user_id, role, joined_at)
            VALUES (?, ?, 'A', ?)
            """,
            (room_id, user_id, now),
        )
    return room_id, invite_code


def join_room(
    user_id: str,
    invite_code: str,
    db_path: str | Path | None = None,
) -> str:
    normalized_code = invite_code.strip().upper()
    if len(normalized_code) != 10 or any(
        char not in _INVITE_ALPHABET for char in normalized_code
    ):
        raise StorageError("err_invite_invalid")
    invite_hash = hashlib.sha256(normalized_code.encode("ascii")).hexdigest()
    now = int(time.time())

    with _connect(db_path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        room = connection.execute(
            "SELECT room_id, invite_expires_at, status FROM rooms WHERE invite_hash = ?",
            (invite_hash,),
        ).fetchone()
        if (
            room is None
            or room["invite_expires_at"] < now
            or room["status"] != "waiting"
        ):
            raise StorageError("err_invite_invalid")
        member_count = connection.execute(
            "SELECT COUNT(*) AS n FROM memberships WHERE room_id = ?",
            (room["room_id"],),
        ).fetchone()["n"]
        already_member = connection.execute(
            "SELECT 1 FROM memberships WHERE room_id = ? AND user_id = ?",
            (room["room_id"], user_id),
        ).fetchone()
        user_exists = connection.execute(
            "SELECT 1 FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        if member_count != 1 or user_exists is None or already_member is not None:
            raise StorageError("err_invite_invalid")

        connection.execute(
            """
            INSERT INTO memberships (room_id, user_id, role, joined_at)
            VALUES (?, ?, 'B', ?)
            """,
            (room["room_id"], user_id, now),
        )
        connection.execute(
            "UPDATE rooms SET status = 'paired' WHERE room_id = ?",
            (room["room_id"],),
        )
    return room["room_id"]


def list_user_rooms(
    user_id: str,
    db_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    with _connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT r.room_id, r.status, r.created_at, mine.role,
                   partner.username AS partner_username
            FROM memberships AS mine
            JOIN rooms AS r ON r.room_id = mine.room_id
            LEFT JOIN memberships AS other
                ON other.room_id = mine.room_id AND other.user_id != mine.user_id
            LEFT JOIN users AS partner ON partner.user_id = other.user_id
            WHERE mine.user_id = ?
            ORDER BY r.created_at DESC
            """,
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_own_summary(
    user_id: str,
    room_id: str,
    db_path: str | Path | None = None,
) -> dict[str, Any] | None:
    with _connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT content, consent, updated_at FROM summaries
            WHERE room_id = ? AND user_id = ?
              AND EXISTS (
                  SELECT 1 FROM memberships
                  WHERE memberships.room_id = summaries.room_id
                    AND memberships.user_id = summaries.user_id
              )
            """,
            (room_id, user_id),
        ).fetchone()
    return dict(row) if row is not None else None


def save_summary(
    user_id: str,
    room_id: str,
    content: str,
    consent: bool,
    db_path: str | Path | None = None,
) -> None:
    value = content.strip()
    if not value or len(value) > MAX_SUMMARY_LENGTH:
        raise StorageError("err_summary_length", max=MAX_SUMMARY_LENGTH)
    now = int(time.time())
    with _connect(db_path) as connection:
        is_member = connection.execute(
            "SELECT 1 FROM memberships WHERE room_id = ? AND user_id = ?",
            (room_id, user_id),
        ).fetchone()
        if is_member is None:
            raise StorageError("err_room_not_found")
        existing = connection.execute(
            "SELECT content, consent FROM summaries WHERE room_id = ? AND user_id = ?",
            (room_id, user_id),
        ).fetchone()
        if (
            existing is not None
            and existing["content"] == value
            and bool(existing["consent"]) == consent
        ):
            return
        connection.execute(
            """
            INSERT INTO summaries (room_id, user_id, content, consent, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(room_id, user_id) DO UPDATE SET
                content = excluded.content,
                consent = excluded.consent,
                updated_at = excluded.updated_at
            """,
            (room_id, user_id, value, int(consent), now),
        )
        connection.execute("DELETE FROM reports WHERE room_id = ?", (room_id,))
        connection.execute(
            "DELETE FROM report_generation WHERE room_id = ?", (room_id,)
        )


def summary_change_clears_report(
    user_id: str,
    room_id: str,
    content: str,
    consent: bool,
    db_path: str | Path | None = None,
) -> bool:
    """Return True if saving this summary would delete the room's shared report."""
    if get_report(user_id, room_id, db_path) is None:
        return False
    existing = get_own_summary(user_id, room_id, db_path)
    return (
        existing is None
        or existing["content"] != content.strip()
        or bool(existing["consent"]) != consent
    )


def get_room_consents(
    user_id: str,
    room_id: str,
    db_path: str | Path | None = None,
) -> dict[str, bool]:
    with _connect(db_path) as connection:
        membership = connection.execute(
            "SELECT role FROM memberships WHERE room_id = ? AND user_id = ?",
            (room_id, user_id),
        ).fetchone()
        if membership is None:
            raise StorageError("err_room_not_found")
        rows = connection.execute(
            """
            SELECT m.role, COALESCE(s.consent, 0) AS consent
            FROM memberships AS m
            LEFT JOIN summaries AS s
                ON s.room_id = m.room_id AND s.user_id = m.user_id
            WHERE m.room_id = ?
            """,
            (room_id,),
        ).fetchall()
    return {row["role"]: bool(row["consent"]) for row in rows}


def get_shared_summaries(
    user_id: str,
    room_id: str,
    db_path: str | Path | None = None,
) -> dict[str, str] | None:
    consents = get_room_consents(user_id, room_id, db_path)
    if consents != {"A": True, "B": True}:
        return None
    with _connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT m.role, s.content
            FROM memberships AS m
            JOIN summaries AS s
              ON s.room_id = m.room_id AND s.user_id = m.user_id
            WHERE m.room_id = ? AND s.consent = 1
            """,
            (room_id,),
        ).fetchall()
    if len(rows) != 2:
        return None
    return {row["role"]: row["content"] for row in rows}


def save_report(
    user_id: str,
    room_id: str,
    report: str,
    db_path: str | Path | None = None,
) -> None:
    value = report.strip()
    if not value:
        raise StorageError("err_report_empty")
    with _connect(db_path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        generation = connection.execute(
            """
            SELECT 1 FROM report_generation
            WHERE room_id = ? AND user_id = ? AND lease_expires_at > ?
            """,
            (room_id, user_id, int(time.time())),
        ).fetchone()
        membership = connection.execute(
            "SELECT 1 FROM memberships WHERE room_id = ? AND user_id = ?",
            (room_id, user_id),
        ).fetchone()
        consent_count = connection.execute(
            """
            SELECT COUNT(*) AS n FROM memberships AS m
            JOIN summaries AS s
              ON s.room_id = m.room_id AND s.user_id = m.user_id
            WHERE m.room_id = ? AND s.consent = 1
            """,
            (room_id,),
        ).fetchone()["n"]
        member_count = connection.execute(
            "SELECT COUNT(*) AS n FROM memberships WHERE room_id = ?",
            (room_id,),
        ).fetchone()["n"]
        if membership is None:
            raise StorageError("err_room_not_found")
        if generation is None:
            raise StorageError("err_report_stale")
        if member_count != 2 or consent_count != 2:
            raise StorageError("err_consent_required")
        connection.execute(
            """
            INSERT INTO reports (room_id, content, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT (room_id) DO NOTHING
            """,
            (room_id, value, int(time.time())),
        )
        connection.execute(
            "DELETE FROM report_generation WHERE room_id = ?", (room_id,)
        )


def get_report(
    user_id: str,
    room_id: str,
    db_path: str | Path | None = None,
) -> str | None:
    with _connect(db_path) as connection:
        membership = connection.execute(
            "SELECT 1 FROM memberships WHERE room_id = ? AND user_id = ?",
            (room_id, user_id),
        ).fetchone()
        if membership is None:
            raise StorageError("err_room_not_found")
        row = connection.execute(
            "SELECT content FROM reports WHERE room_id = ?", (room_id,)
        ).fetchone()
    return row["content"] if row is not None else None


def delete_room(
    user_id: str,
    room_id: str,
    db_path: str | Path | None = None,
) -> None:
    with _connect(db_path) as connection:
        membership = connection.execute(
            "SELECT 1 FROM memberships WHERE room_id = ? AND user_id = ?",
            (room_id, user_id),
        ).fetchone()
        if membership is None:
            raise StorageError("err_room_not_found")
        connection.execute("DELETE FROM rooms WHERE room_id = ?", (room_id,))
