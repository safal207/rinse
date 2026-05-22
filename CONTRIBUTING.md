# Contributing to RINSE

Thanks for your interest in contributing to RINSE.

RINSE is a small, deterministic reflection layer that reads traces, derives interpretations, and keeps source truth untouched. Before you open a PR, please read the main design note in [`docs/RINSE.md`](docs/RINSE.md).

## Core invariant

```text
RINSE may forget an interpretation.
RINSE must never erase the trace that made the interpretation possible.
```

This is the project's hard boundary. Contributions should preserve trace immutability and keep the reference pipeline easy to inspect.

## Local setup

Start with the commands requested in the project issue:

```bash
python -m compileall rinse examples
python -m unittest discover -s tests -v
python -m rinse.core examples/rinse/sample_input.json
```

If you are working from the current examples-based scaffold, the runnable entrypoint is also available here:

```bash
python examples/rinse/rinse_core.py examples/rinse/sample_input.json
```

## Contribution guidelines

- Keep the implementation deterministic where possible.
- Do not mutate, redact, or delete source traces.
- Prefer focused PRs over broad refactors.
- Do not add LLM or external API dependencies unless they are explicitly discussed first.
- Update tests or docs whenever behavior, interfaces, or contributor workflow changes.

## Pull request checklist

Before opening a PR, please confirm:

- [ ] Source traces are not mutated.
- [ ] Tests or docs are updated.
- [ ] No LLM/API dependency is added unless explicitly discussed.
- [ ] Deterministic behavior is preserved where possible.
- [ ] The change is scoped and explained clearly in the PR body.

## Suggested workflow

1. Sync with the latest `main`.
2. Create a short-lived branch for one change.
3. Make the smallest change that solves the issue.
4. Run the relevant verification commands.
5. Open a PR with context, tradeoffs, and any follow-up work.

Small, readable improvements are preferred here.
