"""Helper script for Hermes to trigger an immediate Feature Dash."""
import argparse
import sys
import os

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from src.hermes.agent import HermesCIAgent

def main():
    parser = argparse.ArgumentParser(description="Run Hermes Feature Dash")
    parser.add_argument("--repo", required=True, help="Repository ID")
    parser.add_argument("--batch", type=int, default=3, help="Proposal batch size")
    args = parser.parse_args()

    agent = HermesCIAgent()
    res = agent.run_feature_dash(args.repo, batch_size=args.batch)
    if not res.get("success"):
        print(f"[!] Preflight Failed: {res.get('reason')}")
        sys.exit(1)

    print(f"[*] Generated {len(res.get('proposals', []))} proposals for {args.repo}")
    for p in res.get("proposals", []):
        print(f"  - [{p['id']}] {p['title']} (Delta: {p['semantic_delta_score']}, Safety: {p['safety_score']})")

if __name__ == "__main__":
    main()
