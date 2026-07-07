"""Quick manual smoke test. The free (rules-only) path runs with no API key
needed. The paid path (personalize=True) requires ANTHROPIC_API_KEY."""
import json

from app.agent.orchestrator import run

# Example: aging parent living alone with no documents -- should route to the
# highest-priority profile per the clinical routing rules.
example_flags = {
    "hasAgingParent": True,
    "parentHasNoDocs": True,
    "parentLivesAlone": True,
}

if __name__ == "__main__":
    free_result = run(example_flags, member_first_name="Elisa", personalize=False)
    print("=== FREE (zero tokens) ===")
    print(json.dumps(free_result, indent=2))

    # Uncomment once ANTHROPIC_API_KEY is set up:
    # paid_result = run(example_flags, member_first_name="Elisa", personalize=True)
    # print("\n=== PAID (personalized) ===")
    # print(json.dumps(paid_result, indent=2))
