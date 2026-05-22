---
name: Feature request
about: Propose a focused RINSE capability
labels: enhancement
---

## What capability are you requesting?

Describe the smallest useful capability you want to add.

## Why is this useful?

Explain the trace, interpretation, or contributor workflow this improves.

## Does this change deterministic behavior?

- [ ] No, behavior remains deterministic.
- [ ] Yes, deterministic output may change.
- [ ] I am not sure.

If deterministic output changes, update or propose golden fixtures.

## Does this touch source traces?

- [ ] No, it only reads source traces or writes derived records.
- [ ] Yes, it changes source traces.
- [ ] I am not sure.

RINSE must never mutate, redact, or delete source traces.

## Proposed acceptance criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Tests or docs are updated.
