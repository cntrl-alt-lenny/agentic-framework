# Spirit Caller: first results of the light-workflow pilot

Recorded 2026-10-06. This is an evidence record and a proposal to evaluate,
not a change to the shared framework or instructions for other projects.
The owner authorized recording the findings on GitHub. No framework release,
rollout, merge-rule change or new automation is authorized by this document.

## Project, release and commits

- Project: `cntrl-alt-lenny/gx-spirit-caller`.
- Installed framework: 3.1.0.
- Before the trial: `5a660035d6faef87902b9f51793b1aff91fa64f9`.
- Trial policy merged in [PR #1635](https://github.com/cntrl-alt-lenny/gx-spirit-caller/pull/1635),
  commit `eb25a961c8975e9ffd410d194c48255f61401397`.
- First matching batch merged in [PR #1636](https://github.com/cntrl-alt-lenny/gx-spirit-caller/pull/1636),
  commit `a42868fb3da2340a96423f56ef52900b9e7500ff`.
- Trial period: 6 to 20 October 2026. Its override expires unless the owner
  extends it.

## Observed problem and intended outcome

The owner reported spending more time coordinating agents and improving the
framework than developing products. Inspection of Spirit Caller's merged
history found its last pre-trial commit touching `src/`, `libs/`, `include/`,
`config/` or `assets/` on 1 September 2026. Later merged work covered framework
adoption, housekeeping and checker improvements. On 6 October, that was a
35-day gap in merged game-source/build-configuration work. This does not
establish that no work occurred on unmerged branches or other machines.

The recorded EUR natural-C baseline remained 414,738 bytes (17.38%). The
intended outcome was more verified matching progress with fewer owner
handoffs, while retaining the project's correctness requirements.

Checker work can be useful. The problem under evaluation is whether making
more process and tooling work prerequisites delays useful matching work.

## What the project changed

The pilot is an explicit temporary override in the project's own `AGENTS.md`.
It leaves framework-owned files and the shared framework repository's
operating instructions unchanged.

1. Brain dispatches one Worker with a short objective, boundaries and checks
   for a meaningful batch of related matching work.
2. Matching batches do not require round folders, formal briefs, or the
   framework's `start` and `report` commands.
3. The Worker attempts multiple functions, commits small, tests and repairs
   failures before handoff. A short summary is stored in
   `docs/batches/<batch>.md`; attempts stay in the existing ledger.
4. A separate Verifier reviews the delivered commit, actual source and
   evidence once per batch, storing `docs/batches/<batch>-review.md`.
5. Ordinary review corrections remain within the batch. A materially changed
   objective or assumption may require a new brief.
6. The owner receives one approval request per reviewed batch. Executors and
   Verifiers still do not merge.
7. Further checker rounds, source-tree consolidation and an unattended
   matching factory are paused as prerequisites to ordinary matching work.

Existing matches, symbols, ROMs, checksums and verification baselines remain
protected. Applicable three-region gates, reference checks and matching
checks remain mandatory. Neither unit tests nor an increased progress figure
substitutes for ROM verification. Baselines remain shrink-only.

## First batch: repository evidence

Batch 01 targeted previously unattempted EUR main functions represented only
as assembly, at most 256 bytes each, in one address region. Of 92 candidates,
37 were attempted: 31 shipped and six were parked.

| Measure | Recorded result |
|---|---|
| New C files / removed assembly files | 31 / 31 |
| New ledger rows | 37: 31 shipped, six parked |
| Natural-C gain | 3,608 bytes |
| Natural-C before / after | 414,738 / 418,346 bytes |
| Headline before / after | 17.38% / 17.53% |
| Reference and fake-match baselines | Unchanged, according to the review |

The source diff and ledger were independently inspected when preparing this
record. Counts and shipped-byte totals agree with the reports. The Worker
reports writing drafts by hand and iterating with existing `fastmatch.py`,
without using the automatic drafting loop or changing the tools.

The committed [Worker summary](https://github.com/cntrl-alt-lenny/gx-spirit-caller/blob/a42868fb3da2340a96423f56ef52900b9e7500ff/docs/batches/batch-01.md)
and [Verifier review](https://github.com/cntrl-alt-lenny/gx-spirit-caller/blob/a42868fb3da2340a96423f56ef52900b9e7500ff/docs/batches/batch-01-review.md)
contain the function list and detailed evidence. The Verifier records:

- Independent `fastmatch` checks at 100% for all 31 new C files.
- Reading every new C file and comparing unusual constructs with the
  original assembly, including constructs the lint alone cannot adjudicate.
- EUR, USA and JPN `SHA1 PASS`; reference and fake-match checks passing;
  `GATE PASS` and final `gate3: GATE EXIT 0`.
- 1,330 pytest tests passed, 15 skipped and 132 subtests passed. No ROM region
  was skipped; pytest skips are distinct from region verification.
- Match-invariant checks reported zero errors and 13,999 warnings. Their
  warning-only exit status was explained rather than described as clean.

These builds and per-function checks were performed by the project agents,
not rerun by the author of this record. The review ran on the delivered
Worker commit; its SHA-1 results are not a separate rerun on the squash-merged
main commit. USA/JPN source was untouched: their passes demonstrate retained
ROM correctness, not new regional C ports.

## Limitations and follow-ups

- One batch is encouraging evidence, not proof of a lasting productivity
  improvement or a causal comparison. Candidate selection, tooling readiness
  and available effort also affect results. Historical success rates are not
  forecasts for untouched functions.
- The Verifier found `func_0203244c` omitted within the report's claimed
  address-order walk. Its disposition needs recording; later batches must
  derive remaining candidates instead of blindly resuming at the reported
  next address. The merged summary still contains that claim at the commit
  inspected here.
- Six parked functions' best percentages and compiler-wall explanations were
  not independently reproduced. They are Worker observations, not verified
  matching results.
- Local struct names are inferred. The review notes inconsistent callback
  prototypes and separate struct views to reconcile before shared-header
  work. No source correction is implied by this evidence record.
- Existing checker reviews document lint blind spots. A green lint result is
  not proof that every new C construct is legitimate. Keep source review at
  the batch boundary; this is not a requirement to restart checker redesign.
- Fresh worktrees needed ignored matching-tool dependencies copied from the
  prepared checkout; the Verifier also needed `dsd.exe`. These setup facts
  are machine-specific. Do not copy Windows paths into Mac instructions.
- Drafting can produce line-ending changes. Cleanup must preserve previous
  successful edits in shared files such as `delinks.txt`, reverting only the
  current attempt's changes. Generated outputs may be produced by build tools
  but must not be deliberately hand-edited to satisfy verification.
- Total owner coordination time and complete message counts have not been
  established. The first batch's delivery alone does not prove that burden
  fell by a particular amount.

## Persistence across Windows, Mac and later agents

The pilot does not depend on the Windows Brain's conversation memory. The
following files are already committed to Spirit Caller's main branch:

| Durable information | Repository location |
|---|---|
| Rules and precedence of the temporary override | `AGENTS.md` |
| Trial dates, evaluation criteria and historical baseline | `docs/state.md` |
| Worker results and limitations | `docs/batches/batch-01.md` |
| Independent review and findings | `docs/batches/batch-01-review.md` |
| Per-function outcomes | `docs/ledger/attempts.tsv` |

A Mac or another machine receives the same policy when its checkout includes
those commits and its agent reads the repository instructions. Before work,
inspect the current branch, uncommitted changes and remote state. Preserve
local work and incorporate the current main branch into the intended working
branch without resets or overwriting another seat's work. An old checkout or
a stale conversation does not automatically gain the new policy. Build-tool
readiness on Windows does not establish readiness on Mac.

This findings document is supplementary evidence. It does not replace the
project's committed instructions, and a review branch is not a main-branch
policy change.

## Transfer to other projects: proposal, not rollout

The potentially reusable pattern is a coherent product batch, short
instructions, small commits, repair within the batch, independent review at
delivery and one owner approval. Each project's definition of done must
remain specific to its risks.

| Project | Suitable batch | Acceptance and review focus |
|---|---|---|
| Spirit Caller | Related function matches | Exact matching, all three ROMs, source legitimacy, preserved references |
| EDOPro Next | One usable feature and its related fixes | UI interaction, regression tests, platform limits and relevant upstream behaviour |
| Retro Formats | A coherent research question or data update | Sources support claims, uncertainty is explicit, provenance and generated-data checks |

Passing software tests cannot prove a historical claim. A ROM checksum cannot
prove UI usability. Large batches should remain coherent enough to review;
unrelated changes should not be bundled merely to reduce handoffs. Licensing,
data-loss risks and public releases still require review before delivery.

No pilot has been authorized or implemented for the other projects through
this record. Do not distribute new mandatory instructions to every Brain or
change the shared framework on the strength of this first result alone.

## Evaluation and next action

Continue the Spirit Caller pilot through 20 October, then evaluate merged,
gate-passed functions and natural-C bytes, owner messages/time, any
regressions or lost matches, and complete recording of failures. Use existing
records and short summaries rather than creating another reporting system.

If progress and coordination improve repeatedly, propose project-specific
pilots elsewhere. Use those results to decide whether a smaller shared policy
is worthwhile. Any future change still follows the repository's merge rule.

## Commands to reproduce the repository inspection

From a Spirit Caller checkout with the relevant main history fetched:

```text
git log --format="%cs %s" 5a660035d6faef87902b9f51793b1aff91fa64f9 -- src libs include config assets
git show eb25a961c8975e9ffd410d194c48255f61401397 -- AGENTS.md docs/state.md
git diff --name-status 5a660035d6faef87902b9f51793b1aff91fa64f9 a42868fb3da2340a96423f56ef52900b9e7500ff -- src config
git show a42868fb3da2340a96423f56ef52900b9e7500ff:docs/ledger/attempts.tsv
git show a42868fb3da2340a96423f56ef52900b9e7500ff:docs/batches/batch-01.md
git show a42868fb3da2340a96423f56ef52900b9e7500ff:docs/batches/batch-01-review.md
```

Expected inspection result: 31 C files added and their 31 assembly files
removed, with 37 `batch-01` ledger rows, 31 shipped rows totalling 3,608 bytes
and six parked rows. The policy commit changes only the two project-owned
instruction/state files. These commands inspect durable evidence; they do
not rerun ROM validation. Rerun the applicable project checks with its
documented toolchain and owner-supplied ROMs to establish a new build verdict.
