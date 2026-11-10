from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

# Drawn on a 24px grid, 2px round stroke, so they read as one family.
ICONS = {
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/>',
    "home": '<path d="M4 11l8-7 8 7v9h-5v-6H9v6H4z"/>',
    "currently": '<circle cx="12" cy="12" r="8.5"/><path d="M10 8.5l5.5 3.5-5.5 3.5z"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "library": '<path d="M5 4h4v16H5zM13 4h4l2.5 16h-4z"/>',
    "feed": '<rect x="4" y="4" width="16" height="16" rx="2"/><path d="M4 15h16"/>',
    "chevron": '<path d="M6 9l6 6 6-6"/>',
    "heart": (
        '<path d="M12 20s-7.5-4.6-9.2-9.2C1.6 7.3 3.8 4.5 7 4.5c2 0 3.8 1.1 5 3 1.2-1.9 3-3 5-3 '
        '3.2 0 5.4 2.8 4.2 6.3C19.5 15.4 12 20 12 20z"/>'
    ),
    "comment": '<path d="M4 5h16v11H9l-5 4z"/>',
    "back": '<path d="M15 5l-7 7 7 7"/>',
    "check": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "copy": '<rect x="8" y="8" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 012-2h9"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4.5 20c1.3-3.6 4-5 7.5-5s6.2 1.4 7.5 5"/>',
    "alert": '<path d="M12 4l9 16H3z"/><path d="M12 10v4M12 17.2v.1"/>',
    "gift": (
        '<path d="M4 11h16v9H4zM3 7h18v4H3zM12 7v13M12 7C10 3 6 3 6 5.5 6 7 8 7 12 7zM12 7c2-4 6-4 '
        '6-1.5C18 7 16 7 12 7z"/>'
    ),
    "crown": '<path d="M3 19L2 7l6 4 4-7 4 7 6-4-1 12z"/>',
    "bounty": '<circle cx="12" cy="10.5" r="4"/><path d="M6 3v18M12 3v18M18 3v18"/>',
    "bell": '<path d="M18 9a6 6 0 10-12 0c0 6-2.5 8-2.5 8h17S18 15 18 9z"/><path d="M10 20a2.2 2.2 0 004 0"/>',
    "x": '<path d="M5 5l14 14M19 5L5 19"/>',
"cog": (
        '<circle cx="12" cy="12" r="3"/>'
        '<path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06 '
        'a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09 '
        'A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83 '
        'l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09 '
        'A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0 '
        'l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09 '
        'a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83 '
        'l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2 '
        'h-.09a1.65 1.65 0 00-1.51 1z"/>'
    ),
}


@register.simple_tag
def icon(name, size=23):
    paths = ICONS[name]
    return format_html(
        '<svg width="{0}" height="{0}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        "{1}</svg>",
        size,
        # ICONS is a fixed table in this file, never user input.
        mark_safe(paths),  # noqa: S308
    )


@register.filter
def bounty_left(delta):
    """A bounty's time_left as a short label: `13d left`, `5h left`, or `Expired`."""
    if delta is None:
        return ""
    seconds = delta.total_seconds()
    if seconds <= 0:
        return "Expired"
    if seconds >= 86400:
        return f"{int(seconds // 86400)}d left"
    return f"{max(1, int(seconds // 3600))}h left"
