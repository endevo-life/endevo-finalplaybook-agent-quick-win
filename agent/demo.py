"""Quick manual smoke test. Trial tier runs with no API key needed.
Paid tier requires ANTHROPIC_API_KEY (or `ant auth login`)."""
import json

from orchestrator import run

# Example: aging parent living alone with no documents -- should route to the
# highest-priority profile per Niki's rules.
example_flags = {
    "hasAgingParent": True,
    "parentHasNoDocs": True,
    "parentLivesAlone": True,
}

if __name__ == "__main__":
    trial_result = run(example_flags, member_first_name="Elisa", tier="trial")
    print("=== TRIAL (zero tokens) ===")
    print(json.dumps(trial_result, indent=2))

    # Uncomment once ANTHROPIC_API_KEY / `ant auth login` is set up:
    # paid_result = run(example_flags, member_first_name="Elisa", tier="paid")
    # print("\n=== PAID (personalized) ===")
    # print(json.dumps(paid_result, indent=2))
