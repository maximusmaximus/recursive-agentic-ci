"""Helper script to ingest a raw stack trace and map to repository AST."""
import argparse
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from src.patterns.telemetry import TelemetryIngestor

def main():
    parser = argparse.ArgumentParser(description="Ingest stack trace for Hermes bug-fix dash")
    parser.add_argument("--file", help="Path to text file containing raw stack trace")
    parser.add_argument("--trace", help="Raw stack trace string")
    parser.add_argument("--type", default="UnhandledException", help="Exception type")
    args = parser.parse_args()

    content = ""
    if args.file and os.path.exists(args.file):
        with open(args.file, "r", encoding="utf-8") as f:
            content = f.read()
    elif args.trace:
        content = args.trace
    else:
        print("[!] Provide either --file or --trace")
        sys.exit(1)

    ingestor = TelemetryIngestor()
    entry = ingestor.ingest_raw_stacktrace(content, args.type)
    print("\n[*] Telemetry Crash Recorded:")
    print(f"  • Exception:   {entry['exception_type']}")
    print(f"  • Module:      {entry['module']}")
    print(f"  • Line:        {entry['line_number']}")
    print(f"  • Function:    {entry['function']}")
    print("Ready to generate crash fix proposal in next sprint dash!\n")

if __name__ == "__main__":
    main()
