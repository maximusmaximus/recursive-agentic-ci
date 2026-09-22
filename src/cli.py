"""Operator Command Line Interface (CLI) for Hermes Recursive Agentic CI.

Allows service administrators and operators to audit repositories, trigger dashes,
launch the web dashboard server, and manage background workers.
"""
import argparse
import json
import sys
from .core.analyzer import RepoAnalyzer
from .hermes.agent import HermesCIAgent
from .server.app import run_server
from .telegram.bot import TelegramHITLBot

def main():
    parser = argparse.ArgumentParser(
        description="Hermes Recursive CI Scaffolding (HITL with Venice AI & Telegram)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Audit command
    audit_parser = subparsers.add_parser("audit", help="Audit a target repository AST & vectors")
    audit_parser.add_argument("--path", required=True, help="Filesystem path to target repository")

    # Dash command
    dash_parser = subparsers.add_parser("dash", help="Trigger a feature & mutation sprint dash")
    dash_parser.add_argument("--repo", required=True, help="Repository ID")
    dash_parser.add_argument("--path", default=None, help="Repository path (if registering on the fly)")
    dash_parser.add_argument("--batch", type=int, default=3, help="Number of proposals")

    # Server command
    server_parser = subparsers.add_parser("server", help="Run the Web Dashboard and MCP API server")
    server_parser.add_argument("--host", default="0.0.0.0", help="Binding host")
    server_parser.add_argument("--port", type=int, default=18880, help="Port to listen on")

    # Bot command
    bot_parser = subparsers.add_parser("bot", help="Run the Telegram HITL bot long-polling daemon")

    # Status command
    status_parser = subparsers.add_parser("status", help="Display registered repositories & system health")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    agent = HermesCIAgent()

    if args.command == "audit":
        analyzer = RepoAnalyzer(args.path)
        report = analyzer.audit()
        print("\n=======================================================")
        print(f" REPOSITORY AUDIT REPORT: {args.path}")
        print("=======================================================")
        print(f"• Total Files:        {report['total_files']}")
        print(f"• Total Lines:        {report['total_lines']}")
        print(f"• Test Suites:        {report['test_suite_count']} ({', '.join(report['test_frameworks'])})")
        print(f"• Health Score:       {report['health_score']}%")
        print(f"• Feature Vectors:    {len(report['feature_vectors'])}")
        print(f"• Mutation Vectors:   {len(report['mutation_bug_vectors'])}\n")
        print("Discovered Feature Vectors:")
        for v in report["feature_vectors"]:
            print(f"  [+] {v['title']} (Impact: {v['impact']})")
        print("\nDiscovered Mutation Resilience Vectors:")
        for v in report["mutation_bug_vectors"][:3]:
            print(f"  [~] {v['title']}")
        print("=======================================================\n")

    elif args.command == "dash":
        if args.path:
            agent.register_repo(args.repo, args.repo, args.path)
        res = agent.run_feature_dash(args.repo, batch_size=args.batch)
        print("\n=======================================================")
        print(f" HERMES FEATURE SPRINT DASH: {args.repo}")
        print("=======================================================")
        if not res.get("success"):
            print(f"[!] Preflight Failed: {res.get('reason')}")
            sys.exit(1)
        for i, prop in enumerate(res.get("proposals", []), 1):
            print(f"\nPROPOSAL #{i} [{prop['id']}]:")
            print(f"Title:         {prop['title']}")
            print(f"Type:          {prop['type'].upper()}")
            print(f"Rationale:     {prop['rationale']}")
            print(f"Safety Score:  {prop['safety_score']}")
            print(f"Delta Score:   {prop['semantic_delta_score']}")
        print("\n=======================================================\n")

    elif args.command == "server":
        run_server(args.host, args.port, agent)

    elif args.command == "bot":
        bot = TelegramHITLBot(agent=agent)
        bot.start_polling()

    elif args.command == "status":
        repos = agent.state.list_repos()
        resources = agent.resources.get_resource_snapshot()
        print("\n=======================================================")
        print(" HERMES RECURSIVE CI SYSTEM STATUS")
        print("=======================================================")
        print(f"• Active Repositories: {len(repos)}")
        for r in repos:
            print(f"  - {r['id']}: Health {r['health_score']}%, Path: {r['path']}")
        print(f"• Token Burn Today:    {resources['tokens_consumed_today']} / {resources['daily_token_quota']}")
        print(f"• Free Disk Space:     {resources['disk_free_gb']} GB")
        print("=======================================================\n")

if __name__ == "__main__":
    main()
