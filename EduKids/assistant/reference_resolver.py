"""Resolve implicit references in user messages using recent session context.

The heuristics are intentionally simple: if the user message contains pronouns
or vague references (ex: "ses livres", "C'est quoi ses livres ?", "Qu'est-ce que ça ?")
we try to make the reference explicit using the session's current_topic or recent
history. This helps the LLM to correctly disambiguate short follow-up questions.
"""
import re


PRONOUN_KEYWORDS = [
    'il', 'elle', 'ils', 'elles', 'leur', 'leurs', 'lui', 'eux', 'ça', 'ce', 'cela',
    'ses', "son", "sa", 'ses', 'son', 'sa', 'ses', 'le', 'la', 'les'
]


def _looks_implicit(message: str) -> bool:
    m = message.lower()
    # crude check: contains short demonstratives/pronouns or starts with interrogative + pronoun
    if any(k in m.split() for k in PRONOUN_KEYWORDS):
        # also exclude cases where a named entity is present (capitalized word)
        if re.search(r"[A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜÇ][a-zàâäéèêëïîôöùûüç'-]{2,}", message):
            return False
        return True
    return False


def resolve_reference(message: str, session: dict) -> str:
    """Return a message rewritten to be explicit when necessary.

    If the message looks like an implicit reference and session contains a
    current_topic, we prepend an explicit reference like "À propos de <topic>: ..."
    Otherwise we return the original message.
    """
    if not message or not session:
        return message

    if not _looks_implicit(message):
        return message

    topic = session.get('current_topic')
    # If topic looks like a phrase 'Sujet: X et Y' produced by classifier, try to extract key part
    if topic:
        # strip leading 'Sujet:' or 'Sujet'
        t = re.sub(r'^[sS]ujet\s*:?', '', topic).strip()
        if t:
            # Build an explicit phrasing suitable for children
            return f"À propos de {t}: {message}"

    # fallback: try to extract last capitalized token from history
    for sender, text in reversed(session.get('history', [])):
        if not text:
            continue
        m = re.search(r"([A-ZÀÂÄÉÈÊËÏÎÔÖÙÛÜÇ][a-zàâäéèêëïîôöùûüç'-]{2,})", text)
        if m:
            return f"À propos de {m.group(1)}: {message}"

    # no context to resolve -> return original
    return message
