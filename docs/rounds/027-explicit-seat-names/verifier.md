<!-- fw-report
round: 027-explicit-seat-names
role: verifier
branch: verifier/027-explicit-seat-names
head: d6093b6a265ac0b752a864f680cbdbeba5f8fc3c
os: macOS 27.0
python: 3.9.6
written: 2026-10-03T18:09:24Z
-->
Reviewed commit: `d6093b6a265ac0b752a864f680cbdbeba5f8fc3c`.
Blind first pass completed before opening `builder.md`.

## Findings

None. All five acceptance criteria are met:

1. `framework/roles/brain.md:28-33` preserves exact generated prompts,
   explicitly uses the project's role name (including Builder), and says
   a specialty never replaces the seat.
2. The guidance distinguishes seat from assignment without creating roles.
   Verifier dispatch remains conditional on Tier 2, after the Worker finishes.
   Seat authority and Brain's prohibition on implementation are unchanged.
3. After the independent pass, the Builder report's illustrative labels were
   confirmed: two Workers remain Workers; a Worker/Verifier pair names different
   seats. The disposable fixture reproduces Worker, declared Builder, and
   Verifier CLI openings. These are evidence, not replacement prompt formats.
4. The card stays at 656 words against a 750-word budget. The introduction
   falls from 44 to 32 words; the dispatch bullet grows from 48 to 60 words.
   The saved zero-context diff matches the actual git diff byte for byte.
5. Required local checks pass at the exact delivered commit. No new tests,
   tools, templates, other cards, state, version, or changelog changes exist.
   Existing prompt tests check behavior that could regress; they do not test
   the new prose. Their passing result alone cannot prove wording clarity.

### Independently reproduced evidence

`python3 -m unittest discover -s tests -t . -v` — exit 0. Real summary:

```text
Ran 83 tests in 121.464s

OK
```

This includes migration, safe-update, prompt, word-budget, and personal-data
checks. `python3 tools/fw.py check` — exit 0:

```text
0 error(s), 0 warning(s)
```

`git diff --check` and `git diff --check origin/main HEAD` — each exit 0,
no output. `git diff --name-status origin/main HEAD` — exit 0; only the
Brain card and this round's brief, Builder report, and attachments differ.
`git diff --numstat origin/main HEAD -- framework/roles/brain.md` — exit 0:

```text
9	8	framework/roles/brain.md
```

An independent inline Python run using `tests.helpers.RoundTest` and `fw`
created a disposable adopted project, ran the actual CLI for each role,
asserted exit 0, and counted the card with `len(text.split())` — exit 0:

```text
role=worker exit=0
Demo · ROUND 027 · WORKER
You are the Worker for Demo, round 027-explicit-seat-names.
role=builder exit=0
Demo · ROUND 027 · BUILDER
You are the Builder for Demo, round 027-explicit-seat-names.
role=verifier exit=0
Demo · ROUND 027 · VERIFIER
You are the Verifier for Demo, round 027-explicit-seat-names.
Brain words: before=656 after=656 budget=750
Words removed=35 added=35
```

The last line counts token replacements using `difflib.ndiff`; net paragraph
counts above separately show the twelve-word offset.
`python3 docs/rounds/027-explicit-seat-names/attachments/prompt_openings.py`
— exit 0. This additionally declares Builder in the fixture's role table:

```text
python3 tools/fw.py prompt --round 027-seat-labels --role worker → exit 0
Demo · ROUND 027 · WORKER
You are the Worker for Demo, round 027-seat-labels.

python3 tools/fw.py prompt --round 027-seat-labels --role builder → exit 0
Demo · ROUND 027 · BUILDER
You are the Builder for Demo, round 027-seat-labels.

python3 tools/fw.py prompt --round 027-seat-labels --role verifier → exit 0
Demo · ROUND 027 · VERIFIER
You are the Verifier for Demo, round 027-seat-labels.
```

Illustrations for surrounding explanation, not substitute prompts:

```text
Two Worker assignments:
Worker — interface implementation
Worker — campaign implementation

Worker/Verifier pair:
Worker — interface implementation
Verifier — independent review

Project-declared executor:
Builder — interface implementation
```

Final production diff, from
`git diff --unified=0 origin/main HEAD -- framework/roles/brain.md` — exit 0:

```diff
diff --git a/framework/roles/brain.md b/framework/roles/brain.md
index c6c816f..c4e9b6c 100644
--- a/framework/roles/brain.md
+++ b/framework/roles/brain.md
@@ -3,4 +3,3 @@
-You hold the project's context, choose the next piece of work, write the
-brief, judge what comes back, and merge under the project's merge rule. The
-owner decides what and why; you make sure what lands is correct, and explain
-it in plain English.
+You hold context, choose work, write briefs, judge results, and merge
+under the project's merge rule. The owner decides what and why; you ensure
+what lands is correct and explain it plainly.
@@ -29,4 +28,6 @@ it in plain English.
-- Give the owner each seat's prompt as one code block, exactly as
-  `python3 tools/fw.py prompt --round <id> --role <role>` prints it, with
-  the project's own role names. For Tier 2, give the Verifier prompt too and
-  say plainly: **send this one only after the Worker has finished.**
+- Give each seat's prompt in one code block exactly as
+  `python3 tools/fw.py prompt --round <id> --role <role>` prints it.
+  Identify the framework seat by its project role name (such as Builder);
+  a task specialty never replaces it. Put details in the brief or
+  surrounding explanation. For Tier 2, include the Verifier prompt:
+  **send this only after the Worker finishes.**
```

### Source and report comparison

Read issue #37 directly on GitHub and via
`gh api repos/cntrl-alt-lenny/agentic-framework/issues/37` — exit 0.
Its triage says `does not claim a reproduced tool defect`; its requested
outcome is explicit seat identification, and its timing authorizes no release
exception. The issue has the documentation label. This supports a wording
round, not a claim that the source project's tool was defective.

The Builder report agrees with independently reproduced scope, counts,
prompts, and local check results. Its earlier suite was run before final
evidence commits; this review supplies a full run at the delivered commit.
No contradictory or unproven implementation claim was found.

`gh api repos/cntrl-alt-lenny/agentic-framework/commits/d6093b6a265ac0b752a864f680cbdbeba5f8fc3c/check-runs`
— exit 0. Observed successful completed checks include the six Linux,
Windows, and macOS Python 3.9/3.12 combinations, ruff, and framework
invariants. Additional check runs at the same commit were still running
for Windows Python 3.9/3.12; macOS and Linux additional runs had succeeded.
These are observed CI results, distinct from the local evidence above.

## Not verified

- Completion of all additional CI runs and required-check settings.
- The source project's installed release and project commit; neither is
  supplied. The original exchange was not reproduced at that project.
- Future agent compliance with the prose and owner interpretation in practice.
- No release, tag, adopter update, or freeze exception was performed or assessed.

## Verdict

The small wording refinement meets the brief with high confidence. It makes
seat identification explicit, preserves generated dispatches and authority,
and offsets all added words. Independent local checks pass at the reviewed
commit. Brain must still make its exact-commit acceptance decision and follow
the owner's merge rule; this review neither merges nor authorizes a release.
