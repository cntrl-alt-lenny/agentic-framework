# 03-feedback-recheck

Path: Checked, because the findings concern shared installer safety and
privacy claims. This batch gathers evidence; it changes no implementation
and ships no release. The source baseline is published v4.0.1 at
06a7d45e45751c40809d6644ea4503ec61cef709.

## Builder dispatch

agentic-framework · BATCH 03-feedback-recheck · BUILDER

Read AGENTS.md, framework/FRAMEWORK.md, framework/roles/worker.md,
docs/state.md and this brief from origin/brain/project-refresh-2026-10-08.
Fetch origin. Work from the latest default branch on worker/03-feedback-recheck
in an isolated checkout; preserve existing work. Run python3 tools/fw.py status.

Establish whether open issues #31, #36 and #43 still reproduce with the
published 4.0.1 tool. Use throwaway project-shaped fixtures and synthetic
personal data. For #31, compare UTF-8, UTF-16LE and UTF-16BE attachments,
including batch and legacy-round locations; distinguish a missed check from
an actual disclosure. For #36, establish whether a deleted hook stays absent
across repeated updates and whether the manifest remains misleading. For
#43, inspect current cleanup guidance and reproduce Git's refusal on a clean,
merged fixture with a tracked, initialized submodule; preserve dirty work.

Do not edit framework/, tools/, templates/, project checkouts or repository
settings. Do not delete existing branches/checkouts, publish, merge, or
change issue labels. This is evidence for Brain's triage, not authority for
a release. Technical questions go to Brain.

Run python3 -m unittest discover -s tests -t . -v,
python3 -m ruff check --select F,E9,B,UP --target-version py39 tools templates tests,
and python3 tools/fw.py check. Retain actual commands, output, exit status
and the literal tested commit. Commit a reproducible evidence script and
sanitized outputs under docs/batches/03-feedback-recheck/; write
docs/batches/03-feedback-recheck.md with Done, Checked, Not checked, Failed
or blocked, at most 500 prose words. Push, name the delivery commit, and
stop editing while it is reviewed. Report on every exit.

## Verifier dispatch — send only after the Builder finishes

agentic-framework · BATCH 03-feedback-recheck · VERIFIER

Read AGENTS.md, framework/FRAMEWORK.md, framework/roles/verifier.md and this
brief. Fetch origin/worker/03-feedback-recheck, resolve and record its literal
delivery commit, and review that frozen commit in an isolated checkout.
If the Builder is still editing, stop and report the question to Brain.

Read the diff before the summary. Independently rerun the three issue
reproductions and the required suite, lint and framework check. Establish
whether each claim follows from current 4.0.1 behaviour; distinguish missing
evidence, misleading records, privacy exposure and data-loss paths. Check
that evidence uses synthetic data and no existing project or checkout was
modified. Findings need a severity, location and reproducible failure path.

Change only docs/batches/03-feedback-recheck-review.md, recording the exact
commit reviewed, real commands/output/exit status, findings and verdict,
within 500 prose words. Commit and push the review on the Builder's branch
after confirming its delivery commit has not moved. Do not fix code, merge,
publish or change issue labels. Send technical questions to Brain. End with
the batch, seat, result and pushed commit.
