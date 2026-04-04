"""Content moderation — filter profanity and slurs from user-generated text."""
import re

# Words that should never appear in reviews/status notes
_BLOCKED_WORDS = {
    'fuck', 'fucker', 'fucking', 'fucked', 'fck', 'fuk', 'fuking',
    'shit', 'shit', 'bullshit', 'shitty', 'sht',
    'ass', 'asshole', 'assholes', 'dumbass',
    'bitch', 'bitches', 'btch',
    'damn', 'damned', 'goddamn',
    'dick', 'dicks', 'dickhead',
    'cunt', 'cunts',
    'bastard', 'bastards',
    'whore', 'slut', 'hoe',
    'retard', 'retarded', 'tard',
    'faggot', 'fag', 'fags',
    'nigger', 'nigga', 'negro',
    'spic', 'chink', 'gook', 'kike', 'wetback',
    'crap', 'piss', 'pissed',
    'stfu', 'gtfo', 'lmfao', 'wtf', 'af',
    'moron', 'idiot', 'stupid',
    'kill', 'murder', 'die',
}

# Compile a single regex pattern for efficient matching
_WORD_BOUNDARY_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(w) for w in sorted(_BLOCKED_WORDS, key=len, reverse=True)) + r')\b',
    re.IGNORECASE
)

# Leet-speak substitutions to catch evasion
_LEET_MAP = str.maketrans({'0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't', '@': 'a', '$': 's'})


def contains_profanity(text):
    """Check if text contains blocked words. Returns (is_clean, matched_word)."""
    if not text:
        return True, None
    # Check original text
    match = _WORD_BOUNDARY_PATTERN.search(text)
    if match:
        return False, match.group(0)
    # Check leet-speak decoded version
    decoded = text.translate(_LEET_MAP)
    if decoded != text:
        match = _WORD_BOUNDARY_PATTERN.search(decoded)
        if match:
            return False, match.group(0)
    return True, None


def clean_text(text, max_length=2000):
    """Sanitize user text: strip, truncate, check profanity.
    Returns (cleaned_text, is_clean, matched_word)."""
    if not text:
        return '', True, None
    text = str(text).strip()[:max_length]
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    is_clean, matched = contains_profanity(text)
    return text, is_clean, matched
