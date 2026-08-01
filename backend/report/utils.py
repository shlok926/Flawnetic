"""
report/utils.py
---------------
Text sanitization utilities for PDF report generation.

These functions ensure all text output to FPDF2 is safe for Latin-1 encoding.
Root cause: FPDF2 default fonts (Helvetica, Times, Courier) are Latin-1 only.
Any Unicode character above U+00FF will raise FPDFUnicodeEncodingException.

Solution: Sanitize ALL strings at the PDF rendering boundary.
This is NOT a workaround — this is the correct approach for FPDF2 with
Latin-1 core fonts. Alternative (DejaVu TTF font) requires bundling font files
which adds deployment complexity. Latin-1 sanitization is simpler and reliable.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Complete Unicode → Latin-1 safe replacement map
UNICODE_REPLACEMENTS = {
    # Dashes
    '\u2014': '-',    # em dash —
    '\u2013': '-',    # en dash –
    '\u2012': '-',    # figure dash ‒
    '\u2015': '-',    # horizontal bar ―
    # Quotes
    '\u2018': "'",    # left single quotation mark '
    '\u2019': "'",    # right single quotation mark '
    '\u201a': ',',    # single low-9 quotation mark ‚
    '\u201b': "'",    # single high-reversed-9 quotation mark ‛
    '\u201c': '"',    # left double quotation mark "
    '\u201d': '"',    # right double quotation mark "
    '\u201e': '"',    # double low-9 quotation mark „
    '\u201f': '"',    # double high-reversed-9 quotation mark ‟
    # Ellipsis
    '\u2026': '...',  # horizontal ellipsis …
    # Bullets and symbols
    '\u2022': '*',    # bullet •
    '\u2023': '>',    # triangular bullet ‣
    '\u25cf': '*',    # black circle ●
    '\u25cb': 'o',    # white circle ○
    # Arrows
    '\u2192': '->',   # rightwards arrow →
    '\u2190': '<-',   # leftwards arrow ←
    '\u2194': '<->',  # left right arrow ↔
    # Check marks / X marks
    '\u2713': 'OK',   # check mark ✓
    '\u2714': 'OK',   # heavy check mark ✔
    '\u2717': 'FAIL', # ballot x ✗
    '\u2718': 'FAIL', # heavy ballot x ✘
    # Currency
    '\u20ac': 'EUR',  # euro sign €
    '\u00a3': 'GBP',  # pound sign £ (already latin-1 but mapping for safety)
    # Other common problematic chars
    '\u00a0': ' ',    # non-breaking space
    '\u00ad': '-',    # soft hyphen
    '\ufeff': '',     # BOM
    '\u200b': '',     # zero width space
    # Emoji (common ones from AI output)
    '\U0001f534': '[CRITICAL]',  # 🔴
    '\U0001f7e0': '[HIGH]',      # 🟠
    '\U0001f7e1': '[MEDIUM]',    # 🟡
    '\U0001f535': '[LOW]',       # 🔵
    '\U0001f7e2': '[PASS]',      # 🟢
    '\u26a0': '[WARN]',          # ⚠
    '\u2139': '[INFO]',          # ℹ
}


def sanitize_text(text: Optional[str], max_length: Optional[int] = None) -> str:
    """
    Sanitize a string for safe rendering in FPDF2 with Latin-1 core fonts.
    
    This function must be called on EVERY string before passing to FPDF2.
    It is NOT optional. Missing a single call can crash PDF generation.
    
    Args:
        text: Input string (can be None, will return empty string)
        max_length: Optional truncation length (None = no limit)
    
    Returns:
        Latin-1 safe string suitable for FPDF2 rendering
    
    Example:
        >>> sanitize_text("Found — 3 issues")
        'Found - 3 issues'
        >>> sanitize_text(None)
        ''
    """
    if text is None:
        return ""
    
    text = str(text)
    
    # Apply known Unicode replacements
    for unicode_char, replacement in UNICODE_REPLACEMENTS.items():
        text = text.replace(unicode_char, replacement)
    
    # Final safety net: encode to latin-1, replacing any remaining problem chars
    try:
        text = text.encode('latin-1', errors='replace').decode('latin-1')
    except Exception as e:
        logger.warning(f"sanitize_text encoding fallback triggered: {e}")
        # Nuclear option: strip everything non-ASCII
        text = text.encode('ascii', errors='replace').decode('ascii')
    
    # Truncate if requested
    if max_length and len(text) > max_length:
        text = text[:max_length - 3] + '...'
    
    return text


def sanitize_url(url: Optional[str], max_length: int = 80) -> str:
    """Sanitize a URL for PDF display — truncate long URLs gracefully."""
    if not url:
        return "N/A"
    url = sanitize_text(url)
    if len(url) > max_length:
        return url[:max_length - 3] + '...'
    return url


def sanitize_steps(steps) -> list[str]:
    """Sanitize a list or dict of reproduction steps."""
    if not steps:
        return ["No steps recorded."]
    
    if isinstance(steps, dict):
        result = []
        for k, v in steps.items():
            result.append(sanitize_text(f"{k}: {v}"))
        return result
    
    if isinstance(steps, list):
        return [sanitize_text(str(step)) for step in steps if step]
    
    return [sanitize_text(str(steps))]
