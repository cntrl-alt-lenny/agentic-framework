<!-- fw-report
round: 027-explicit-seat-names
role: builder
branch: builder/027-explicit-seat-names
head: 3b38c6b75d07dd16d9eabb8b1b36531767a20ba7
os: macOS 27.0
python: 3.9.6
written: 2026-10-03T16:52:32Z
-->
## Verified

The wording change is commit `ffd38ebd1032b17105167a86dbc0a152f223fba7`;
reportable work and evidence are at `3d643a5aae1d439fc55feae97ba230913abeecc6`.
All results below are local, not CI results.

- `python3 -m unittest discover -s tests -t . -v` — exit 0.
  Started at `ffd38eb`; subsequent commit added only round evidence while it ran.
  Real output:

```text
Ran 83 tests in 99.062s

OK
```

- `python3 tools/fw.py check` at `3d643a5` — exit 0:

```text
0 error(s), 0 warning(s)
```

- `git diff --check` at `3d643a5` — exit 0, no output.
- `python3 docs/rounds/027-explicit-seat-names/attachments/prompt_openings.py`
  at `3d643a5` — exit 0. Uses the existing disposable adopted-project
  fixture and the actual CLI; declares Builder in its AGENTS role table.
  Each generated opening was asserted against the actual output:

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

Existing `tests/test_round.py` prompt tests passed in the full suite;
`seat_prompt` already generates the role header and seat introduction.
No tool defect is claimed.

- Counted with `len(text.split())`, as in `tests/test_docs.py`, comparing
  `ffd38eb^:framework/roles/brain.md` and the committed card:

```text
Brain card words: before 656, after 656, budget 750
Introduction: before 44, after 32 (12 removed)
Dispatch bullet: before 48, after 60 (12 added)
```

The exact wording diff from `git diff --unified=0 ffd38eb^ ffd38eb -- framework/roles/brain.md`
is recorded verbatim in `docs/rounds/027-explicit-seat-names/attachments/brain.diff`.
It changes only the introduction and dispatch bullet; other guidance is intact.
Zero context lines avoid trailing spaces in the saved diff. A final range diff
check found whitespace in the original attachment; this attachment corrects it.

Illustrative opening labels for the surrounding explanation (evidence of how
seat and specialty can be distinguished, not replacement prompts):

```text
Two Worker assignments:
Worker — interface implementation
Worker — campaign implementation

Worker/Verifier pair:
Worker — interface implementation
Verifier — independent review

Project-declared executor name:
Builder — interface implementation
```

Both first labels remain Workers; specialties create no standing seats.
The second pair distinguishes implementation from review. Verifier dispatch
remains conditional on Tier 2, with the existing send order preserved.
The generated prompt itself remains exactly as printed; details belong in
its brief or surrounding explanation.

## Not verified

- CI at the delivered commit, independent Verifier review, and Brain acceptance
  have not been observed. Local checks do not substitute for them.
- The source project's installed release and commit are unknown. Issue #37
  supplies wording evidence, not a reproduced tool defect.
- No tag, release, adopter update, or change to the release freeze was performed.
- A full-suite run at the final report commit will follow the report push;
  the recorded full-suite output above is from the implementation check.

## Changed

- `framework/roles/brain.md`: explicitly identify the framework seat using
  its project role name, prohibit specialty replacing it, and place details
  in the brief or explanation. Trim the introduction to offset all added words.
- `docs/rounds/027-explicit-seat-names/attachments/brain.diff`: exact card diff.
- `docs/rounds/027-explicit-seat-names/attachments/prompt_openings.py`:
  reproducible disposable-fixture evidence, with no new production tests.
- `docs/rounds/027-explicit-seat-names/builder.md`: this report.
- `docs/state.md` was unchanged.

## Open questions

None for implementation. Independent Verifier review and Brain judgment remain
for the normal Tier 2 handoff. Accepted wording belongs in the next eligible
release batch; this round does not authorize release activity.
