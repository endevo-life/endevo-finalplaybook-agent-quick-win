"""The branded HTML shell: escaping, client compatibility, and the text/HTML pair.

These guard the properties that make mail render in real inboxes -- not the
exact markup, which should be free to change.
"""
import pytest
from fastapi.testclient import TestClient

from app.data import email as email_mod
from app.data.events import reset_events
from app.data.store import reset_store
from app.main import create_app
from app.services import email_template as T
from app.services import notifications


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    """Fresh store, events, and email transport per test -- same shape as
    test_notifications.py."""
    reset_store()
    reset_events()
    email_mod.reset_email()
    monkeypatch.setenv("EMAIL_BACKEND", "console")
    monkeypatch.setenv("OPERATOR_EMAILS", "ops@example.com")
    yield
    reset_store()
    reset_events()
    email_mod.reset_email()


@pytest.fixture
def client():
    return TestClient(create_app())


def sent():
    return email_mod.last_sends(limit=50)


# ── The shell itself ─────────────────────────────────────────────────────────
def test_shell_is_a_complete_document():
    html = T.shell("My Final Playbook", T.heading("Hi"))
    assert html.startswith("<!DOCTYPE html>")
    assert "</html>" in html
    assert "My Final Playbook" in html


def test_no_inline_svg_anywhere():
    """Gmail, Outlook and Yahoo strip inline SVG -- the logo must not need it."""
    html = T.shell("My Final Playbook", T.heading("Hi"))
    assert "<svg" not in html.lower()


def test_layout_uses_tables_not_flexbox():
    """Outlook renders through Word's engine: no flexbox, no grid."""
    html = T.shell("My Final Playbook", T.heading("Hi"))
    assert "<table" in html
    for unsupported in ("display:flex", "display:grid", "flex-direction"):
        assert unsupported not in html.replace(" ", "")


def test_styles_are_inline_not_in_a_style_block():
    """A <style> block is stripped by Gmail in several views; inline survives."""
    html = T.shell("My Final Playbook", T.heading("Hi") + T.detail_rows([("A", "b")]))
    assert "<style" not in html.lower()
    assert 'style="' in html


def test_card_width_is_email_safe():
    html = T.shell("My Final Playbook", T.heading("Hi"))
    assert 'width="600"' in html  # widest that survives Outlook's reading pane


def test_preheader_is_hidden_in_the_body():
    html = T.shell("My Final Playbook", T.heading("Hi"), preheader="Peek at this")
    assert "Peek at this" in html
    assert "display:none" in html


# ── Escaping: member text reaches these templates ────────────────────────────
def test_member_text_is_escaped():
    html = T.quote_block("<script>alert('x')</script> & \"quoted\"")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "&amp;" in html


def test_escaping_applies_to_detail_values_and_headings():
    html = T.detail_rows([("Email", "<b>a@b.com</b>")]) + T.heading("<i>hi</i>")
    assert "<b>" not in html and "<i>" not in html
    assert "&lt;b&gt;" in html and "&lt;i&gt;" in html


def test_detail_rows_drop_empty_values():
    """Callers pass optional fields unconditionally; blanks must not render."""
    html = T.detail_rows([("Kept", "yes"), ("Dropped", ""), ("AlsoDropped", None)])
    assert "Kept" in html
    assert "Dropped" not in html


def test_button_is_omitted_without_a_url():
    assert T.button("Open", "") == ""
    assert "href" in T.button("Open", "https://example.com")


# ── Every notification ships both parts ──────────────────────────────────────
def test_signup_email_has_both_text_and_html(client):
    client.post("/api/auth/start", json={"email": "new@example.com"})
    msg = sent()[0]
    assert msg["body"], "text part is required -- spam scoring and a11y read it"
    assert msg["html"].startswith("<!DOCTYPE html>")
    # the same fact appears in both parts
    assert "new@example.com" in msg["body"]
    assert "new@example.com" in msg["html"]


def test_feedback_email_has_both_parts_and_quotes_the_member(client):
    client.post("/api/feedback", json={"kind": "complaint",
                                       "message": "The tone felt cold.",
                                       "email": "m@example.com"})
    msg = sent()[-1]
    assert "The tone felt cold." in msg["body"]
    assert "The tone felt cold." in msg["html"]
    assert msg["html"].startswith("<!DOCTYPE html>")


def test_digest_has_both_parts():
    result = notifications.send_weekly_digest()
    assert result["sent"] is True
    msg = sent()[-1]
    assert msg["body"] and msg["html"].startswith("<!DOCTYPE html>")


def test_html_carries_the_brand():
    """The logo, product name and footer are what make it look like ours."""
    html = T.shell("My Final Playbook", T.heading("Hi"))
    assert T.BRAND["brand"] in html        # navy header band
    assert T.BRAND["book_teal"] in html    # the drawn book mark
    assert "Live Fully" in html            # footer tagline


def test_privacy_line_holds_in_the_html_part(client):
    """Same guarantee as the text part: identity only, never plan content."""
    client.post("/api/auth/start", json={"email": "private@example.com"})
    html = sent()[0]["html"].lower()
    for leak in ("answers", "narrative", "diagnosis", "funeral"):
        assert leak not in html
