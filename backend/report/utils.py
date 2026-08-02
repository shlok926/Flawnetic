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


COLORS = {
    "header_bg": (15, 23, 42),      # #0F172A dark slate
    "header_text": (255, 255, 255), # white
    "critical": (239, 68, 68),      # #EF4444 red
    "high": (249, 115, 22),         # #F97316 orange
    "medium": (234, 179, 8),        # #EAB308 yellow
    "low": (59, 130, 246),          # #3B82F6 blue
    "code_bg": (241, 245, 249),     # #F1F5F9 light grey
    "border": (203, 213, 225),      # #CBD5E1
    "text_primary": (15, 23, 42),   # #0F172A
    "text_secondary": (100, 116, 139), # #64748B
    "success": (34, 197, 94),       # #22C55E green
}


def compute_risk_score(findings: list) -> float:
    """
    Weighted risk score 0-10:
    Critical = 10 points each
    High     = 5 points each
    Medium   = 2 points each  
    Low      = 0.5 points each
    Score = min(10.0, weighted_sum / normalizer)
    """
    if not findings:
        return 0.0
    weights = {"CRITICAL": 10.0, "HIGH": 5.0, "MEDIUM": 2.0, "LOW": 0.5}
    total = sum(weights.get(str(f.get("severity", "LOW")).upper(), 0.5) for f in findings)
    return round(min(10.0, (total / max(len(findings), 1)) * 1.5 + (total * 0.2)), 1)


def get_risk_label(score: float) -> tuple:
    """Returns (label, color_rgb_tuple) for risk score."""
    if score >= 8.0:
        return ("CRITICAL RISK", COLORS["critical"])
    if score >= 6.0:
        return ("HIGH RISK", COLORS["high"])
    if score >= 4.0:
        return ("MEDIUM RISK", COLORS["medium"])
    if score >= 2.0:
        return ("LOW RISK", COLORS["low"])
    return ("MINIMAL RISK", COLORS["success"])


def format_code_snippet(payload: str, max_length: int = 200) -> str:
    """Format a payload/code snippet for display in PDF code box."""
    if not payload:
        return "N/A"
    cleaned = sanitize_text(payload)
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length] + "..."
    return cleaned


def truncate_text_smart(text: str, limit: int = 300) -> str:
    """Truncate text at sentence boundary for cleaner PDF display."""
    if not text or len(text) <= limit:
        return sanitize_text(text or "")
    truncated = sanitize_text(text[:limit])
    last_period = truncated.rfind('.')
    if last_period > int(limit * 0.7):
        return truncated[:last_period + 1]
    return truncated + "..."

