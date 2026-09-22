# Anti-Abuse, Anti-Gamification & Threat Model Whitepaper

Continuous integration systems that autonomously propose code modifications face serious risks of runaway recursion, vanity commit farming, resource exhaustion, and prompt injection. This document details the threat model and defense layers implemented in the Hermes Recursive CI framework.

---

## 1. Threat Vectors

### A. Vanity Commit Farming & Activity Gamification
- **Threat**: Agents or malicious actors gaming GitHub contribution graphs, PR counts, or line-count metrics by generating cosmetic PRs (e.g. reordering imports, changing whitespace, rephrasing docstrings).
- **Impact**: Codebase churn, noisy git history, wasted maintainer review fatigue.
- **Mitigation**:
  - **Semantic Delta Scorer**: Evaluates code deltas on an impact spectrum. Cosmetic phrases receive heavy negative penalties (`-0.25`).
  - **Symmetry Requirement**: Proposals must touch both implementation and unit test files to earn sufficient delta scores (`>= 0.45`).

### B. Infinite Recursive Loops & Token Bleed
- **Threat**: Autonomous agents continually rewriting their own code or generating endless variations of identical features, burning thousands of LLM dollars.
- **Impact**: API quota exhaustion, denial of service.
- **Mitigation**:
  - **Daily Hard-Caps**: Enforced limits on daily token burn (default: `250,000` tokens) and max proposals per day (default: `5`).
  - **Cooldown Windows**: Mandatory interval (default: 60 minutes) between automated dash runs for any single repository.

### C. Maintainer Rejection Aversion & Circuit Breakers
- **Threat**: Agent repeatedly suggests an architectural pattern that the team has previously disliked or banned.
- **Mitigation**:
  - **Rejection Rationale Extraction**: When a maintainer clicks `Reject`, Hermes records the human rationale and converts it into a hard negative constraint (`DO NOT: ...`).
  - **Circuit Breaker**: If 3 consecutive proposals for a repository are rejected, automated runs are halted for 7 days.

### D. Silent Main Branch Corruption
- **Threat**: Code that hallucinated an import or broke an untested edge case gets merged into main.
- **Mitigation**:
  - **Hermetic Sandbox Worktrees**: All proposed code is copied into temporary scratch workspaces.
  - **100% Test Gate**: The candidate code must run and pass all test suites before it can ever be marked `TESTS_PASSED`.
