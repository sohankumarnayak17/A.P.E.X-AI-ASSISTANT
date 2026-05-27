import re

# ══════════════════════════════
#   APEX — Helper Utilities
# ══════════════════════════════

def extract_yt_term(command: str) -> str:
    """Extract search term from 'play X on youtube' style commands."""
    command = command.strip()
    # Pattern: play ... on youtube
    match = re.search(r"play\s+(.+?)\s+on\s+youtube", command, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Pattern: youtube play ...
    match = re.search(r"youtube\s+play\s+(.+)", command, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Pattern: play ... youtube
    match = re.search(r"play\s+(.+?)\s+youtube", command, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


def remove_words(text: str, words_to_remove: list) -> str:
    """Remove specific words from a string (case-insensitive)."""
    stop = {w.lower() for w in words_to_remove}
    return " ".join(w for w in text.split() if w.lower() not in stop)


def clean_query(query: str, remove: list = None) -> str:
    """Lowercase, strip, and optionally remove filler words."""
    q = query.lower().strip()
    if remove:
        q = remove_words(q, remove)
    return q


def extract_name_from_query(query: str, keywords: list) -> str:
    """Extract a name after a keyword. E.g. 'call john' → 'john'."""
    q = query.lower()
    for kw in keywords:
        if kw in q:
            name = q.split(kw, 1)[-1].strip()
            if name:
                return name
    return ""