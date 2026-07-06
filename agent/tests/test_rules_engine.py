"""Unit tests for the deterministic routing engine. No server, no API key,
no network -- these must all pass with only requirements.txt installed."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rules_engine import MemberContext, build_plan, match_profiles, MAX_ACTION_ITEMS_PER_PLAN
from orchestrator import run


def test_aging_parent_is_highest_priority():
    ctx = MemberContext(hasAgingParent=True, parentHasNoDocs=True, postDivorce=True)
    matched = match_profiles(ctx)
    assert matched["lead"] == "profile_aging_parent"


def test_post_divorce_beats_young_children():
    ctx = MemberContext(postDivorce=True, hasYoungChildren=True, noWill=True)
    matched = match_profiles(ctx)
    assert matched["lead"] == "profile_post_divorce_life_change"


def test_young_children_requires_no_will():
    ctx = MemberContext(hasYoungChildren=True, noWill=False)
    matched = match_profiles(ctx)
    assert matched["lead"] != "profile_young_children"


def test_solo_ager_requires_assets():
    ctx = MemberContext(isSoloAger=True, hasAssets=False)
    matched = match_profiles(ctx)
    assert matched["lead"] != "profile_solo_ager"


def test_pressure_test_before_clean_slate():
    ctx = MemberContext(hasWill=True, hasNothingDone=True)  # contradictory but pressure-test should win
    matched = match_profiles(ctx)
    assert matched["lead"] == "profile_pressure_test"


def test_business_owner_runs_in_parallel_not_as_lead_override():
    ctx = MemberContext(hasNothingDone=True, isBusinessOwner=True)
    matched = match_profiles(ctx)
    assert matched["lead"] == "profile_clean_slate"
    assert "profile_business_owner" in matched["parallel"]


def test_no_flags_matches_nothing():
    ctx = MemberContext()
    matched = match_profiles(ctx)
    assert matched["lead"] is None
    assert matched["parallel"] == []


def test_action_items_are_capped():
    ctx = MemberContext(hasAgingParent=True, parentHasNoDocs=True)
    plan = build_plan(ctx)
    assert len(plan["actionItems"]) <= MAX_ACTION_ITEMS_PER_PLAN


def test_business_action_items_are_capped():
    ctx = MemberContext(isBusinessOwner=True, hasNothingDone=True)
    plan = build_plan(ctx)
    assert len(plan["businessActionItems"]) <= MAX_ACTION_ITEMS_PER_PLAN


def test_matched_action_items_carry_scripts_where_defined():
    ctx = MemberContext(hasAgingParent=True, parentHasNoDocs=True)
    plan = build_plan(ctx)
    assert any("script" in item for item in plan["actionItems"])


def test_no_flags_no_llm_call():
    """Empty plan with personalize=True must not reach the LLM -- see guardrails.md."""
    result = run({}, member_first_name="Test", personalize=True)
    assert result["plan"]["leadProfile"] is None
    assert result["personalized"] is None


def test_free_path_never_calls_llm_and_needs_no_dependency():
    """This test intentionally does not require the `anthropic` package to be
    importable to prove the free path has no such dependency at runtime."""
    result = run(
        {"hasAgingParent": True, "parentHasNoDocs": True},
        member_first_name="Elisa",
        personalize=False,
    )
    assert result["tier"] == "free"
    assert "personalized" not in result
