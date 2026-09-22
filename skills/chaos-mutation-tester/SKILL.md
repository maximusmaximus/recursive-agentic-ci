---
name: chaos-mutation-tester
description: "Probes repository resilience and test-suite thoroughness by injecting controlled AST mutations (boundary flips, inverted checks) to detect and eliminate CI blindspots."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [mutation-testing, chaos-engineering, resilience, test-coverage, qa]
---

# Chaos Mutation Tester Skill

Eliminates "test rot" and false confidence by actively proving whether test suites detect real logic regressions.

## When to Use

Activate this skill when:
- Running scheduled security or resilience audits on mission-critical codebases.
- Verifying whether new features have genuine regression protection.
- Checking cryptographic, mathematical, or permission-checking boundary conditions.

## Quick Dispatch

| Task | Command | Description |
|---|---|---|
| **Run Mutation Probe** | `python skills/chaos-mutation-tester/scripts/run_mutation_probe.py --path <repo>` | Injects fault and asserts test failure |
| **Trigger Resilience Dash** | `python skills/recursive-ci/scripts/run_dash.py --repo <id> --batch 3` | Injects mutation vectors into proposal queue |

## How Mutation Testing Works

```
Original Code ──> AST Mutant ──> Run Test Suite in Sandbox
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
         [Tests FAIL: Good!]                             [Tests PASS: Alert!]
   CI harness caught regression                      Blindspot detected in tests
(Mutation killed, suite is healthy)             (Hermes drafts missing boundary test)
```

1. **Mutation Operators**:
   - Invert comparison operators (`<` to `>`, `==` to `!=`).
   - Boundary shifts (`index + 1` to `index`).
   - Remove exception raising (`raise PermissionDenied()` to `pass`).
2. **Outcome Verification**:
   - If tests fail, the mutation was successfully **killed** (system is resilient).
   - If tests pass, a **blindspot** is discovered. Hermes immediately notifies Telegram and drafts the missing unit test!
