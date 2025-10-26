"""Lightweight in-memory session context for conversations.

This provides a simple temporary memory per conversation id without requiring
a database. It's intentionally minimal: a thread-safe dict with timestamps.
"""
from threading import Lock
import time

# session structure: { 'history': [ (sender, text) ... ], 'current_topic': str, 'updated': timestamp }
_sessions = {}
_lock = Lock()

DEFAULT_TTL = 60 * 60 * 3  # 3 hours


def _cleanup_expired():
    now = time.time()
    with _lock:
        to_delete = [k for k, v in _sessions.items() if now - v.get('updated', 0) > DEFAULT_TTL]
        for k in to_delete:
            del _sessions[k]


def get_session(conversation_id: int) -> dict:
    """Return the session dict for a conversation (creates if missing)."""
    _cleanup_expired()
    with _lock:
        s = _sessions.get(conversation_id)
        if not s:
            s = {'history': [], 'current_topic': None, 'updated': time.time()}
            _sessions[conversation_id] = s
        return s


def update_history(conversation_id: int, sender: str, text: str):
    """Append a message to the in-memory history for context use."""
    s = get_session(conversation_id)
    with _lock:
        s['history'].append((sender, text))
        s['updated'] = time.time()


def set_current_topic(conversation_id: int, topic: str):
    s = get_session(conversation_id)
    with _lock:
        s['current_topic'] = topic
        s['updated'] = time.time()


def get_current_topic(conversation_id: int):
    s = get_session(conversation_id)
    return s.get('current_topic')


def clear_session(conversation_id: int):
    with _lock:
        if conversation_id in _sessions:
            del _sessions[conversation_id]


def set_quiz(conversation_id: int, quiz: dict):
    s = get_session(conversation_id)
    with _lock:
        s['quiz'] = quiz
        s['quiz_state'] = {'current': 0, 'correct': 0, 'awaiting_answer': False}
        s['updated'] = time.time()


def get_quiz(conversation_id: int):
    s = get_session(conversation_id)
    return s.get('quiz')


def get_quiz_state(conversation_id: int):
    s = get_session(conversation_id)
    return s.get('quiz_state')


def clear_quiz(conversation_id: int):
    s = get_session(conversation_id)
    with _lock:
        s.pop('quiz', None)
        s.pop('quiz_state', None)
        s['updated'] = time.time()
