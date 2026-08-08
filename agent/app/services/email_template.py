"""Branded HTML shell for outbound mail -- the look, never the words.

Layering, so the split established in this repo holds:

    data/email.py            transport   -- how bytes move (console | ses)
    services/email_template.py  CHROME   -- the frame every message sits in
    services/notifications.py   content  -- what a specific message says

This module owns the frame ONLY: logo, card, footer, colors, spacing. It never
decides what a message says, so a new notification gets the brand for free and
a brand change never touches message copy.

Why a hand-rolled table layout instead of a CSS framework
---------------------------------------------------------
Email clients are not browsers. Outlook renders through Word's HTML engine;
Gmail strips <style> blocks in some views and the whole <head> in others. So:

- Tables for layout, not flexbox/grid (Outlook supports neither).
- Every style INLINE on the element. A <style> block cannot be relied on.
- No inline SVG -- Gmail, Outlook and Yahoo all strip it. The book mark is
  rebuilt from nested divs with background-color + border-radius, which every
  client renders. This is why the logo is code here rather than an <img>: an
  external image needs a public URL and is blocked-by-default in most clients
  ("display images below"), so a hosted logo shows as an empty box to most
  recipients on first open. The drawn mark always renders.
- Colors are copied from frontend/src/styles/global.css :root, so mail matches
  the app. They are duplicated deliberately -- Python cannot read the CSS, and
  a silent drift is better than a build step. See BRAND below.

Every builder returns a complete HTML document as a string. Callers pair it with
a plain-text alternative; see notifications.py.
"""

# Brand tokens -- mirrored from frontend/src/styles/global.css :root.
# Keep in sync by hand; there is no build step between the two.
BRAND = {
    "bg": "#FAFAF9",       # page behind the card
    "surf": "#FFFFFF",     # card face
    "surf2": "#F2F0EC",    # inset panels (stat rows, quoted message)
    "ink": "#141C2E",      # headings
    "body": "#3B4557",     # body copy
    "dim": "#5C6577",      # secondary / footer text (WCAG AA on white)
    "line": "#E3E1D9",     # hairlines
    "brand": "#1B2A4A",    # navy -- header band, logo tile
    "brand_lt": "#E9E2D2", # warm sand -- on-navy text
    "accent": "#B08D57",   # gold -- rules, emphasis
    "danger": "#A6423A",   # complaints, alerts
    # Book-mark palette, from frontend/public/favicon.svg
    "book_teal": "#58BBB6",
    "book_sand": "#D5D1C7",
    "book_ribbon": "#FF5D00",
}

FONT = ("-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, "
        "Helvetica, Arial, sans-serif")

# The app sets headings in Georgia (see .fp-plan7-headline in global.css). Both
# families are preinstalled on Windows and macOS, so no webfont is needed --
# which matters because Outlook ignores @font-face entirely.
SERIF = 'Georgia, "Iowan Old Style", "Times New Roman", serif'

# Where the logo is served from. It must be a PUBLIC, stable URL: mail clients
# fetch it at open time, long after the request that sent it. Overridable via
# EMAIL_LOGO_URL so a white-label deploy points at its own asset.
import os as _os

LOGO_URL = _os.environ.get(
    "EMAIL_LOGO_URL", "https://app.finalplaybook.com/email-logo.png"
)


def _logo_mark(size: int = 44) -> str:
    """The app's logo, as a hosted image.

    This is the SAME mascot the app shows in its top nav (frontend Logo.jsx ->
    assets/jesse_final.png), not the favicon's book mark -- the point is that
    mail and app read as one product, so the email has to use what members
    actually see on screen.

    It is a photographic image, so it cannot be drawn with table cells the way
    a geometric mark could; it has to be fetched from a public URL. Gmail and
    Outlook block remote images until the recipient allows them, so on a first
    open the header may show a gap where this sits. That is a deliberate,
    accepted trade (operators click "display images" once and it sticks for the
    sender). The `alt` text keeps the header meaningful in the meantime.

    Served at 2x (96px) and displayed at `size` so it stays sharp on retina.
    Width/height are set as HTML ATTRIBUTES as well as CSS: Outlook ignores CSS
    dimensions on images and would otherwise render it at full natural size.
    """
    return (
        f'<img src="{_esc(LOGO_URL)}" width="{size}" height="{size}"'
        f' alt="" role="presentation"'
        f' style="width:{size}px;height:{size}px;display:block;border:0;'
        f'outline:none;text-decoration:none;-ms-interpolation-mode:bicubic;">'
    )


def _header(product_name: str, eyebrow: str = "") -> str:
    """Navy band: brandmark, product name, and an optional small label."""
    eyebrow_html = ""
    if eyebrow:
        eyebrow_html = (
            f'<div style="margin-top:6px;font-size:11px;letter-spacing:.09em;'
            f'text-transform:uppercase;color:{BRAND["brand_lt"]};opacity:.85;'
            f'font-family:{FONT};">{_esc(eyebrow)}</div>'
        )
    return (
        f'<tr><td style="background-color:{BRAND["brand"]};padding:24px 32px;'
        f'border-radius:16px 16px 0 0;">'
        f'<table role="presentation" cellpadding="0" cellspacing="0" border="0"'
        f' style="border-collapse:collapse;"><tr>'
        f'<td valign="middle" style="padding-right:14px;font-size:0;'
        f'line-height:0;">{_logo_mark(44)}</td>'
        f'<td valign="middle">'
        # Georgia here to match the app's headline treatment (.fp-plan7-headline)
        f'<div style="font-size:20px;font-weight:700;color:#FFFFFF;'
        f'font-family:{SERIF};line-height:1.25;letter-spacing:-0.01em;">'
        f'{_esc(product_name)}</div>'
        f'{eyebrow_html}'
        f'</td></tr></table>'
        f'</td></tr>'
    )


def _footer(product_name: str, note: str = "") -> str:
    """Closing band. `note` explains why this specific mail was received."""
    note_html = ""
    if note:
        note_html = (
            f'<div style="margin-bottom:8px;color:{BRAND["dim"]};font-size:12px;'
            f'line-height:1.6;font-family:{FONT};">{_esc(note)}</div>'
        )
    return (
        f'<tr><td style="padding:22px 32px 26px;border-top:1px solid {BRAND["line"]};'
        f'background-color:{BRAND["surf2"]};border-radius:0 0 16px 16px;">'
        f'{note_html}'
        f'<div style="color:{BRAND["dim"]};font-size:12px;line-height:1.6;'
        f'font-family:{FONT};">'
        f'<strong style="color:{BRAND["body"]};">{_esc(product_name)}</strong>'
        f' &nbsp;·&nbsp; Live Fully ~ Die Ready.'
        f'</div>'
        f'<div style="margin-top:6px;color:{BRAND["dim"]};font-size:11px;'
        f'line-height:1.6;font-family:{FONT};">'
        f'Operator notification &mdash; sent automatically. Replies to this '
        f'address are not monitored.'
        f'</div>'
        f'</td></tr>'
    )


def shell(product_name: str, inner: str, preheader: str = "",
          eyebrow: str = "", footer_note: str = "") -> str:
    """Wrap message content in the branded card.

    `inner` is trusted HTML the caller has already escaped.
    `preheader` is the grey preview line inboxes show beside the subject; it is
    hidden in the body itself so it never renders twice.
    """
    pre = ""
    if preheader:
        pre = (
            f'<div style="display:none;font-size:1px;color:{BRAND["bg"]};'
            f'line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;">'
            f'{_esc(preheader)}'
            f'&nbsp;&zwnj;' * 1 +
            f'</div>'
        )
    return (
        f'<!DOCTYPE html><html lang="en"><head>'
        f'<meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<meta name="x-apple-disable-message-reformatting">'
        f'<title>{_esc(product_name)}</title>'
        f'</head>'
        f'<body style="margin:0;padding:0;background-color:{BRAND["bg"]};'
        f'-webkit-font-smoothing:antialiased;">'
        f'{pre}'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"'
        f' border="0" style="border-collapse:collapse;background-color:{BRAND["bg"]};">'
        f'<tr><td align="center" style="padding:28px 12px;">'
        # 600px is the widest that survives Outlook's reading pane without
        # horizontal scroll.
        # 16px radius + the app's soft shadow, from .fp-plan7. Outlook ignores
        # both and renders a plain square card, which is fine -- they are polish.
        f'<table role="presentation" width="600" cellpadding="0" cellspacing="0"'
        f' border="0" style="border-collapse:collapse;width:600px;max-width:100%;'
        f'background-color:{BRAND["surf"]};border:1px solid {BRAND["line"]};'
        f'border-radius:16px;'
        f'box-shadow:0 1px 2px rgba(22,31,51,.03),0 12px 30px -22px rgba(22,31,51,.28);">'
        f'{_header(product_name, eyebrow)}'
        f'<tr><td style="padding:30px 32px 26px;">{inner}</td></tr>'
        f'{_footer(product_name, footer_note)}'
        f'</table>'
        f'</td></tr></table>'
        f'</body></html>'
    )


# ── Content blocks ───────────────────────────────────────────────────────────
def heading(text: str, sub: str = "") -> str:
    sub_html = ""
    if sub:
        sub_html = (
            f'<p style="margin:0 0 22px;color:{BRAND["body"]};font-size:15px;'
            f'line-height:1.6;font-family:{FONT};">{_esc(sub)}</p>'
        )
    # Serif headline, matching .fp-plan7-headline in the app.
    return (
        f'<h1 style="margin:0 0 10px;color:{BRAND["ink"]};font-size:23px;'
        f'font-weight:700;line-height:1.25;letter-spacing:-0.01em;'
        f'font-family:{SERIF};">{_esc(text)}</h1>'
        f'{sub_html}'
    )


def detail_rows(rows) -> str:
    """Label/value pairs in an inset panel -- the signup and feedback facts.

    `rows` is [(label, value)]; falsy values are dropped so callers can pass
    optional fields without branching.
    """
    cells = ""
    for label, value in rows:
        if value in (None, ""):
            continue
        cells += (
            f'<tr>'
            f'<td valign="top" style="padding:7px 14px 7px 0;color:{BRAND["dim"]};'
            f'font-size:13px;white-space:nowrap;font-family:{FONT};">{_esc(label)}</td>'
            f'<td valign="top" style="padding:7px 0;color:{BRAND["ink"]};'
            f'font-size:14px;font-weight:500;word-break:break-word;'
            f'font-family:{FONT};">{_esc(str(value))}</td>'
            f'</tr>'
        )
    if not cells:
        return ""
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"'
        f' border="0" style="border-collapse:collapse;background-color:{BRAND["surf2"]};'
        f'border:1px solid {BRAND["line"]};border-radius:10px;margin:0 0 22px;">'
        f'<tr><td style="padding:14px 18px;">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"'
        f' border="0" style="border-collapse:collapse;">{cells}</table>'
        f'</td></tr></table>'
    )


def stat_grid(stats) -> str:
    """Digest numbers as label/value rows with the value right-aligned.

    Deliberately not a multi-column grid: Outlook drops equal-width table cells
    below ~500px and the columns collapse into each other. Rows always work.
    """
    body = ""
    for i, (label, value) in enumerate(stats):
        border = "" if i == 0 else f'border-top:1px solid {BRAND["line"]};'
        body += (
            f'<tr>'
            f'<td style="padding:10px 0;{border}color:{BRAND["body"]};'
            f'font-size:14px;font-family:{FONT};">{_esc(label)}</td>'
            f'<td align="right" style="padding:10px 0;{border}color:{BRAND["ink"]};'
            f'font-size:17px;font-weight:600;font-family:{FONT};'
            f'white-space:nowrap;">{_esc(str(value))}</td>'
            f'</tr>'
        )
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"'
        f' border="0" style="border-collapse:collapse;margin:0 0 24px;">{body}</table>'
    )


def section_title(text: str) -> str:
    """Gold uppercase eyebrow, matching .fp-plan7-eyebrow in the app."""
    return (
        f'<div style="margin:26px 0 12px;padding-bottom:8px;'
        f'border-bottom:1px solid {BRAND["line"]};color:{BRAND["accent"]};'
        f'font-size:12.5px;font-weight:700;letter-spacing:.09em;'
        f'text-transform:uppercase;font-family:{FONT};">{_esc(text)}</div>'
    )


def quote_block(text: str, tone: str = "neutral") -> str:
    """The member's own words, set apart. `tone="alert"` for complaints."""
    edge = BRAND["danger"] if tone == "alert" else BRAND["accent"]
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"'
        f' border="0" style="border-collapse:collapse;background-color:{BRAND["surf2"]};'
        f'border-left:3px solid {edge};border-radius:0 8px 8px 0;margin:0 0 22px;">'
        f'<tr><td style="padding:16px 18px;color:{BRAND["ink"]};font-size:15px;'
        f'line-height:1.65;white-space:pre-wrap;word-break:break-word;'
        f'font-family:{FONT};">{_esc(text)}</td></tr></table>'
    )


def bullet_list(items) -> str:
    if not items:
        return ""
    lis = "".join(
        f'<li style="margin:0 0 7px;color:{BRAND["body"]};font-size:14px;'
        f'line-height:1.6;font-family:{FONT};word-break:break-word;">{_esc(str(i))}</li>'
        for i in items
    )
    return f'<ul style="margin:0 0 22px;padding-left:20px;">{lis}</ul>'


def button(label: str, url: str) -> str:
    """Primary action. Omitted entirely when no URL is configured."""
    if not url:
        return ""
    return (
        f'<table role="presentation" cellpadding="0" cellspacing="0" border="0"'
        f' style="border-collapse:collapse;margin:4px 0 8px;">'
        f'<tr><td align="center" style="background-color:{BRAND["brand"]};'
        f'border-radius:8px;">'
        f'<a href="{_esc(url)}" style="display:inline-block;padding:12px 26px;'
        f'color:#FFFFFF;font-size:14px;font-weight:600;text-decoration:none;'
        f'font-family:{FONT};">{_esc(label)}</a>'
        f'</td></tr></table>'
    )


def note(text: str) -> str:
    return (
        f'<p style="margin:0 0 6px;color:{BRAND["dim"]};font-size:13px;'
        f'line-height:1.6;font-family:{FONT};">{_esc(text)}</p>'
    )


def _esc(s) -> str:
    """Escape for HTML. Member-supplied text (feedback messages, addresses)
    lands in these templates, so nothing interpolated may be trusted."""
    return (
        str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
