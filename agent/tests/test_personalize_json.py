"""Tests for the tolerant JSON extraction used on open-weight (Bedrock) output.

Open-weight models return the right content but often wrap it (code fences,
preambles, trailing commentary). _extract_json_object must recover the object so
the 7-day plan doesn't fail with a raw JSON error the way it did in production.
"""
import json

import pytest

from app.agent.personalize import _extract_json_object

VALID = {"headline": "H", "steps": [], "closing_note": "C"}


def test_clean_json():
    assert _extract_json_object(json.dumps(VALID)) == VALID


def test_preamble_and_trailing_commentary():
    # The exact failure shape seen in production: prose around the object.
    raw = (
        "Here is the plan:\n"
        + json.dumps(VALID)
        + "\nLet me know if you need anything else."
    )
    assert _extract_json_object(raw) == VALID


def test_markdown_code_fence():
    raw = "```json\n" + json.dumps(VALID) + "\n```"
    assert _extract_json_object(raw) == VALID


def test_brace_inside_string_value():
    obj = {"headline": "Use a {fireproof} box", "steps": [], "closing_note": "C"}
    assert _extract_json_object(json.dumps(obj)) == obj


def test_escaped_quote_inside_string():
    obj = {"headline": 'She said "hi"', "steps": [], "closing_note": "C"}
    assert _extract_json_object(json.dumps(obj)) == obj


def test_no_json_raises():
    with pytest.raises(json.JSONDecodeError):
        _extract_json_object("I'm sorry, I can't help with that.")
