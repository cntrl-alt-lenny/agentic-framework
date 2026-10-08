# 02-project-refresh: Brain summary

Path: Small. Refresh project records and the handoff after the 4.0 rollout;
no shared implementation changes.

## Done

- Brought the clean primary checkout from its old round branch to the
  published 4.0.1 default branch, preserving all old branches and checkouts.
- Replaced the obsolete rollout queue in `docs/state.md`; recorded the
  already-completed Spirit Caller adoption and closure of rounds 028/029.
- Removed closed issue #32 from the queue; retained open #31, #36 and #43
  for evidence-led rechecking rather than assuming their 3.x reports still
  establish 4.x failures.
- Prepared batch 03's Builder and Verifier dispatches. Project release
  updates belong to each project's Brain; no adopting checkout was changed.

## Checked

- GitHub release `v4.0.1` points to
  `06a7d45e45751c40809d6644ea4503ec61cef709`.
- Read each adopting project's default-branch manifest on 2026-10-08:

| Project | Recorded release |
|---|---|
| edopro-next | 4.0.0 |
| edopro-retro-formats | 4.0.0 |
| fe6-next | 4.0.0 |
| fire-emblem-awakening-assistant | 4.0.0 |
| gx-spirit-caller | 4.0.0 |
| mgs-mc-modkit | 4.0.0 |

- Issue #32's closure records that rounds 028/029 remain unmerged history.
- Required local check output is retained in `02-project-refresh/checks.log`.

## Not checked

- These manifest observations do not prove current product/runtime quality
  or complete scorecards. Other project Brains are refreshing their work.
- No production installation, release, old-branch deletion, repository
  setting change or merge was performed.
- The separate pilot evidence branch was read but not accepted for merge.

## Failed or blocked

- The bare `ruff` command was unavailable; the installed module runs as
  `python3 -m ruff`.
- The original release CI run marked failure although all six test jobs and
  lint succeeded; its final combined check was absent. Brain retried the
  run once. See the checks log for the refresh's final CI observation.
