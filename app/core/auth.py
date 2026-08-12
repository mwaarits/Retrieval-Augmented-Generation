import json
import secrets

from app.config import get_settings

# Token store in-memory: token -> user_id. Tanpa expiry; hilang saat restart.
_tokens: dict[str, str] = {}


def load_users() -> dict[str, str]:
    """Return {username: password} dari AUTH_USERS (dibaca sekali per proses)."""
    try:
        entries = json.loads(get_settings().auth_users)
    except (json.JSONDecodeError, TypeError):
        return {}
    if not isinstance(entries, list):
        return {}
    return {
        e["username"]: e["password"]
        for e in entries
        if isinstance(e, dict) and e.get("username") and e.get("password")
    }


def authenticate(username: str, password: str) -> str | None:
    if load_users().get(username) == password:
        return username
    return None


def issue_token(user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    _tokens[token] = user_id
    return token


def get_user(token: str) -> str | None:
    return _tokens.get(token)


def revoke_token(token: str) -> None:
    _tokens.pop(token, None)