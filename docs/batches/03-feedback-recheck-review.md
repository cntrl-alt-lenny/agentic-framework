# 03-feedback-recheck — Verifier

Reviewed delivery: `afef0d0dba65e9ec04cda5fe3c8962f68b7c52c5`.
Dispatch: `origin/brain/project-refresh-2026-10-08` at
`738c700e3e0a29b0856ef83302f6d16e899027b7`.
Published baseline: `06a7d45e45751c40809d6644ea4503ec61cef709` (4.0.1).

Verdict: evidence sufficient; all three goals met. No blocking delivery
finding. This records existing product issues for Brain, not implementation
approval. Builder's completed chat confirmed editing stopped; remote tip
remained the delivery commit during review. Diff read before summary; only
five batch evidence/documentation files changed. Product directories match
4.0.1 byte-for-byte. Audited fixture operations target temporary directories;
synthetic identities and payloads only. Existing checkouts remain intact.

Findings against 4.0.1:

- **SHOULD FIX #31**, `tools/fw.py:555`: NUL detection excludes BOM-bearing
  UTF-16LE/BE attachments from scanning. Independently write the same
  synthetic path/email payload into batch and legacy-round attachments:
  UTF-8 yields two errors/exit 1; both UTF-16 variants yield zero/exit 0
  while remaining decodable. This is a missed privacy gate and potential
  exposure if an agent subsequently publishes such an attachment; no actual
  disclosure was established.
- **NOTE #36**, `tools/adopt.py:377,403–409` and generated
  `docs/agents/framework.json`: adopt with hooks, commit hook deletion, then
  repeat dry-run/apply twice. Hook stays absent; manifest retains
  `options.hooks=true` and `{kind: seed}`. The record can mislead as live
  inventory, but also retains deletion history that prevents restoration.
  Neither restoration nor data loss follows; removing the record's safety
  role is not justified by this evidence.
- **SHOULD FIX #43**, `tools/fw.py:457–477` and
  `framework/roles/brain.md:34–35`: a clean initialized-submodule seat whose
  tip is an ancestor of main is advertised removable. Normal removal exits
  128 before and after non-forced deinitialization. Dirty-submodule control
  is excluded from the list and preserves its sentinel after refusal.
  Evidence proves unusable advice, not destructive cleanup.

All 69 tests, lint and framework check passed at the reviewed delivery;
commands, actual outputs and exit statuses follow. An initial review draft
failed one documentation test because adjacent transcript lines were parsed
as a command. Added display gutters to prevent that parsing; no product
change. Text transcripts use a `| ` gutter, not part of command output. Independent reproduction
uses a separately written driver, not Builder assertions. Environment:
macOS arm64, Python 3.9.6, Git 2.55.0. Not checked: Windows/Linux,
no-BOM UTF-16, real disclosure, forced removal, existing adopters or CI.
No implementation fixes, merge, release or issue changes.

## Independent reproduction

Save the following program as `/tmp/fw03-independent.py`; replace
`<REVIEW>` with the isolated delivery checkout. Printed paths/interpreter
are sanitized; command results are otherwise retained.

```python
import codecs
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

SOURCE = Path(sys.argv[1]).resolve()
BASE = '06a7d45e45751c40809d6644ea4503ec61cef709'
ENV = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1',
           GIT_AUTHOR_NAME='Verifier Fixture', GIT_COMMITTER_NAME='Verifier Fixture',
           GIT_AUTHOR_EMAIL='verifier' + '@example.invalid',
           GIT_COMMITTER_EMAIL='verifier' + '@example.invalid')
with tempfile.TemporaryDirectory(prefix='fw03-independent-') as tmp:
    root = Path(tmp)
    def clean(s):
        return s.replace(str(root), '<TMP>').replace(str(SOURCE), '<REVIEW>').replace(sys.executable, 'python3')
    def run(cwd, *args, expected=0, show=True):
        args = [str(a) for a in args]
        result = subprocess.run(args, cwd=cwd, env=ENV, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if show:
            print('$ (' + clean(str(cwd)) + ') ' + clean(subprocess.list2cmdline(args)))
            print(clean(result.stdout).rstrip())
            print('exit:', result.returncode)
        assert result.returncode == expected, result.stdout
        return result.stdout
    release = root / 'release'
    run(root, 'git', 'clone', '--local', '--no-hardlinks', SOURCE, release, show=False)
    run(release, 'git', 'checkout', '--detach', BASE, show=False)
    assert run(release, 'git', 'rev-parse', 'HEAD').strip() == BASE
    def gitinit(p):
        p.mkdir()
        run(p, 'git', 'init', '-b', 'main', show=False)
    def commit(p, msg):
        run(p, 'git', 'add', '.', show=False)
        run(p, 'git', 'commit', '-m', msg, show=False)
    p = root / 'project'
    gitinit(p)
    run(release, sys.executable, 'tools/adopt.py', p, '--project', 'Independent fixture', '--hooks', show=False)
    commit(p, 'Fixture baseline')
    print('Setup: local clone at exact baseline; fresh git project adopted with --hooks; all setup commands exit 0.')
    payload = 'C:' + chr(92) + 'Users' + chr(92) + 'VerifierSynthetic' + chr(92) + 'evidence\n' + 'probe' + '@example.invalid\n'
    for location in ('docs/batches/03-independent/attachments/probe.txt', 'docs/rounds/003-independent/attachments/probe.txt'):
        attachment = p / location
        attachment.parent.mkdir(parents=True, exist_ok=True)
        for enc, bom in [('utf-8', b''), ('utf-16-le', codecs.BOM_UTF16_LE), ('utf-16-be', codecs.BOM_UTF16_BE)]:
            attachment.write_bytes(bom + payload.encode(enc))
            print('CASE', location, enc)
            out = run(p, sys.executable, 'tools/fw.py', 'check', expected=1 if enc == 'utf-8' else 0)
            if enc == 'utf-8':
                assert 'Windows user folder' in out and 'email address' in out
            else:
                assert '0 error(s), 0 warning(s)' in out
                assert attachment.read_bytes()[2:].decode(enc) == payload
            attachment.unlink()
    hook = p / '.githooks/pre-push'
    hook.unlink()
    commit(p, 'Delete hook')
    for cycle in range(1, 3):
        print('HOOK CYCLE', cycle)
        before = (p / 'docs/agents/framework.json').read_bytes()
        run(release, sys.executable, 'tools/adopt.py', p, '--update', '--dry-run')
        assert (p / 'docs/agents/framework.json').read_bytes() == before
        run(release, sys.executable, 'tools/adopt.py', p, '--update')
        manifest = json.loads((p / 'docs/agents/framework.json').read_text())
        assert not hook.exists() and manifest['options']['hooks'] is True
        assert manifest['files']['.githooks/pre-push'] == {'kind': 'seed'}
        print('hook absent; options.hooks=true; record={kind: seed}; manifest unchanged:', (p / 'docs/agents/framework.json').read_bytes() == before)
    sub = root / 'sub'
    gitinit(sub)
    (sub / 'sentinel.txt').write_text('clean synthetic\n')
    commit(sub, 'Submodule baseline')
    run(p, 'git', '-c', 'protocol.file.allow=always', 'submodule', 'add', sub, 'module', show=False)
    (p / '.gitignore').write_text('.worktrees/\n')
    commit(p, 'Track submodule')
    seat = p / '.worktrees/worker-independent'
    run(p, 'git', 'worktree', 'add', '-b', 'worker/independent', seat, show=False)
    run(seat, 'git', '-c', 'protocol.file.allow=always', 'submodule', 'update', '--init', show=False)
    (p / 'advance.txt').write_text('synthetic main advance\n')
    commit(p, 'Advance main')
    print('Submodule setup: tracked initialized module, seat tip behind main; all setup commands exit 0.')
    assert not run(seat, 'git', 'status', '--porcelain', '--untracked-files=all').strip()
    run(p, 'git', 'merge-base', '--is-ancestor', 'worker/independent', 'main')
    assert 'finished checkouts' in run(p, sys.executable, 'tools/fw.py', 'status', '--offline')
    run(p, 'git', 'worktree', 'remove', seat, expected=128)
    run(seat, 'git', 'submodule', 'deinit', 'module')
    run(p, 'git', 'worktree', 'remove', seat, expected=128)
    run(seat, 'git', '-c', 'protocol.file.allow=always', 'submodule', 'update', '--init', show=False)
    sentinel = seat / 'module/sentinel.txt'
    sentinel.write_text('dirty synthetic sentinel\n')
    run(seat, 'git', 'status', '--porcelain', '--untracked-files=all')
    out = run(p, sys.executable, 'tools/fw.py', 'status', '--offline')
    assert 'uncommitted changes in linked checkout' in out and 'finished checkouts' not in out
    run(p, 'git', 'worktree', 'remove', seat, expected=128)
    assert sentinel.read_text() == 'dirty synthetic sentinel\n'
    print('Independent assertions passed; dirty sentinel preserved before temporary-fixture disposal; no force used.')
```

```text
| $ python3 /tmp/fw03-independent.py <REVIEW>
| $ (<TMP>/release) git rev-parse HEAD
| 06a7d45e45751c40809d6644ea4503ec61cef709
| exit: 0
| Setup: local clone at exact baseline; fresh git project adopted with --hooks; all setup commands exit 0.
| CASE docs/batches/03-independent/attachments/probe.txt utf-8
| $ (<TMP>/project) python3 tools/fw.py check
| error: docs/batches/03-independent/attachments/probe.txt:1 contains a Windows user folder; the documents agents read (AGENTS.md, CLAUDE.md, GEMINI.md, docs/state.md, docs/agents/**/*.md, docs/batches/**, and 3.x rounds: docs/rounds/*/*.md and docs/rounds/*/attachments/**) must work on every machine and are public
| error: docs/batches/03-independent/attachments/probe.txt:2 contains an email address; the documents agents read (AGENTS.md, CLAUDE.md, GEMINI.md, docs/state.md, docs/agents/**/*.md, docs/batches/**, and 3.x rounds: docs/rounds/*/*.md and docs/rounds/*/attachments/**) must work on every machine and are public
| 2 error(s), 0 warning(s)
| exit: 1
| CASE docs/batches/03-independent/attachments/probe.txt utf-16-le
| $ (<TMP>/project) python3 tools/fw.py check
| 0 error(s), 0 warning(s)
| exit: 0
| CASE docs/batches/03-independent/attachments/probe.txt utf-16-be
| $ (<TMP>/project) python3 tools/fw.py check
| 0 error(s), 0 warning(s)
| exit: 0
| CASE docs/rounds/003-independent/attachments/probe.txt utf-8
| $ (<TMP>/project) python3 tools/fw.py check
| error: docs/rounds/003-independent/attachments/probe.txt:1 contains a Windows user folder; the documents agents read (AGENTS.md, CLAUDE.md, GEMINI.md, docs/state.md, docs/agents/**/*.md, docs/batches/**, and 3.x rounds: docs/rounds/*/*.md and docs/rounds/*/attachments/**) must work on every machine and are public
| error: docs/rounds/003-independent/attachments/probe.txt:2 contains an email address; the documents agents read (AGENTS.md, CLAUDE.md, GEMINI.md, docs/state.md, docs/agents/**/*.md, docs/batches/**, and 3.x rounds: docs/rounds/*/*.md and docs/rounds/*/attachments/**) must work on every machine and are public
| 2 error(s), 0 warning(s)
| exit: 1
| CASE docs/rounds/003-independent/attachments/probe.txt utf-16-le
| $ (<TMP>/project) python3 tools/fw.py check
| 0 error(s), 0 warning(s)
| exit: 0
| CASE docs/rounds/003-independent/attachments/probe.txt utf-16-be
| $ (<TMP>/project) python3 tools/fw.py check
| 0 error(s), 0 warning(s)
| exit: 0
| HOOK CYCLE 1
| $ (<TMP>/release) python3 tools/adopt.py <TMP>/project --update --dry-run
| update: /private<TMP>/project -> agentic-framework 4.0.1 (from 4.0.1)
|   same    docs/agents/FRAMEWORK.md
|   same    docs/agents/roles/brain.md
|   same    docs/agents/roles/worker.md
|   same    docs/agents/roles/verifier.md
|   same    tools/fw.py
|   same    tests/test_framework.py
|   same    docs/state.md
|   same    docs/batches/README.md
|   same    .gitattributes
|   same    .worktrees/.gitignore
|   keep    AGENTS.md  (project-owned)
|   gone    .githooks/pre-push  (deleted in this project, so not re-created)
| nothing to do: this project already matches agentic-framework 4.0.1
| 
| dry run: nothing written
| exit: 0
| $ (<TMP>/release) python3 tools/adopt.py <TMP>/project --update
| update: /private<TMP>/project -> agentic-framework 4.0.1 (from 4.0.1)
|   same    docs/agents/FRAMEWORK.md
|   same    docs/agents/roles/brain.md
|   same    docs/agents/roles/worker.md
|   same    docs/agents/roles/verifier.md
|   same    tools/fw.py
|   same    tests/test_framework.py
|   same    docs/state.md
|   same    docs/batches/README.md
|   same    .gitattributes
|   same    .worktrees/.gitignore
|   keep    AGENTS.md  (project-owned)
|   gone    .githooks/pre-push  (deleted in this project, so not re-created)
| nothing to do: this project already matches agentic-framework 4.0.1
| exit: 0
| hook absent; options.hooks=true; record={kind: seed}; manifest unchanged: True
| HOOK CYCLE 2
| $ (<TMP>/release) python3 tools/adopt.py <TMP>/project --update --dry-run
| update: /private<TMP>/project -> agentic-framework 4.0.1 (from 4.0.1)
|   same    docs/agents/FRAMEWORK.md
|   same    docs/agents/roles/brain.md
|   same    docs/agents/roles/worker.md
|   same    docs/agents/roles/verifier.md
|   same    tools/fw.py
|   same    tests/test_framework.py
|   same    docs/state.md
|   same    docs/batches/README.md
|   same    .gitattributes
|   same    .worktrees/.gitignore
|   keep    AGENTS.md  (project-owned)
|   gone    .githooks/pre-push  (deleted in this project, so not re-created)
| nothing to do: this project already matches agentic-framework 4.0.1
| 
| dry run: nothing written
| exit: 0
| $ (<TMP>/release) python3 tools/adopt.py <TMP>/project --update
| update: /private<TMP>/project -> agentic-framework 4.0.1 (from 4.0.1)
|   same    docs/agents/FRAMEWORK.md
|   same    docs/agents/roles/brain.md
|   same    docs/agents/roles/worker.md
|   same    docs/agents/roles/verifier.md
|   same    tools/fw.py
|   same    tests/test_framework.py
|   same    docs/state.md
|   same    docs/batches/README.md
|   same    .gitattributes
|   same    .worktrees/.gitignore
|   keep    AGENTS.md  (project-owned)
|   gone    .githooks/pre-push  (deleted in this project, so not re-created)
| nothing to do: this project already matches agentic-framework 4.0.1
| exit: 0
| hook absent; options.hooks=true; record={kind: seed}; manifest unchanged: True
| Submodule setup: tracked initialized module, seat tip behind main; all setup commands exit 0.
| $ (<TMP>/project/.worktrees/worker-independent) git status --porcelain --untracked-files=all
| 
| exit: 0
| $ (<TMP>/project) git merge-base --is-ancestor worker/independent main
| 
| exit: 0
| $ (<TMP>/project) python3 tools/fw.py status --offline
| Framework
|   pinned to agentic-framework 4.0.1 (https://github.com/cntrl-alt-lenny/agentic-framework)
|   newer releases: not checked
| Merge rule
|   owner-approves
| Work not merged yet
|   nothing waiting: every branch is merged
| This machine
|   on main; no uncommitted changes
|   no 'origin' remote: nothing here is backed up anywhere else
|   finished checkouts (clean, and their work is merged) that can be removed: .worktrees/worker-independent -- git worktree remove <folder>
|   safe to leave this machine: NO -- push or deal with the items above first
| Checks
|   all project checks pass
| Command form on this machine: python3 tools/fw.py <command>
| next: nothing is waiting on you; ask Brain for the next batch
| exit: 0
| $ (<TMP>/project) git worktree remove <TMP>/project/.worktrees/worker-independent
| fatal: working trees containing submodules cannot be moved or removed
| exit: 128
| $ (<TMP>/project/.worktrees/worker-independent) git submodule deinit module
| Cleared directory 'module'
| Submodule 'module' (<TMP>/sub) unregistered for path 'module'
| exit: 0
| $ (<TMP>/project) git worktree remove <TMP>/project/.worktrees/worker-independent
| fatal: working trees containing submodules cannot be moved or removed
| exit: 128
| $ (<TMP>/project/.worktrees/worker-independent) git status --porcelain --untracked-files=all
|  M module
| exit: 0
| $ (<TMP>/project) python3 tools/fw.py status --offline
| Framework
|   pinned to agentic-framework 4.0.1 (https://github.com/cntrl-alt-lenny/agentic-framework)
|   newer releases: not checked
| Merge rule
|   owner-approves
| Work not merged yet
|   nothing waiting: every branch is merged
| This machine
|   on main; no uncommitted changes
|   no 'origin' remote: nothing here is backed up anywhere else
|   uncommitted changes in linked checkout /private<TMP>/project/.worktrees/worker-independent
|   safe to leave this machine: NO -- push or deal with the items above first
| Checks
|   all project checks pass
| Command form on this machine: python3 tools/fw.py <command>
| next: nothing is waiting on you; ask Brain for the next batch
| exit: 0
| $ (<TMP>/project) git worktree remove <TMP>/project/.worktrees/worker-independent
| fatal: working trees containing submodules cannot be moved or removed
| exit: 128
| Independent assertions passed; dirty sentinel preserved before temporary-fixture disposal; no force used.
| driver exit: 0
```

## Required checks at reviewed delivery

```text
| $ python3 -m unittest discover -s tests -t . -v
| test_adopt_installs_a_working_project (tests.test_adopt.FreshAdoption) ... ok
| test_adopting_twice_asks_for_update (tests.test_adopt.FreshAdoption) ... ok
| test_existing_files_are_never_overwritten (tests.test_adopt.FreshAdoption) ... ok
| test_a_project_file_left_beside_its_framework_copy_still_counts_as_a_user (tests.test_adopt.LegacyMigration) ... ok
| test_a_project_that_is_not_a_git_repository_is_still_protected (tests.test_adopt.LegacyMigration) ... ok
| test_an_edited_rendered_file_is_kept (tests.test_adopt.LegacyMigration) ... ok
| test_migration_keeps_everything_owned_or_edited (tests.test_adopt.LegacyMigration) ... ok
| test_status_in_a_dormant_2x_project_says_it_must_migrate (tests.test_adopt.LegacyMigration) ... ok
| test_the_new_fw_works_in_the_migrated_project (tests.test_adopt.LegacyMigration) ... ok
| test_users_git_cannot_see_still_protect_a_file (tests.test_adopt.LegacyMigration) ... ok
| test_a_deleted_seed_stays_deleted (tests.test_adopt.RealProjectLayouts) ... ok
| test_a_finished_seat_checkout_is_listed_as_removable (tests.test_adopt.RealProjectLayouts) ... ok
| test_a_seat_file_named_for_the_projects_executor_is_named (tests.test_adopt.RealProjectLayouts) ... ok
| test_a_squash_merged_batch_is_safe_to_leave_on_the_seats_machine (tests.test_adopt.RealProjectLayouts) ... ok
| test_archive_tags_on_the_remote_are_safe_to_leave (tests.test_adopt.RealProjectLayouts) ... ok
| test_only_an_exact_release_tag_is_installed (tests.test_adopt.ReleaseCheck) ... ok
| test_a_dry_run_prints_what_each_release_asks (tests.test_adopt.UpdateOutput) ... ok
| test_an_up_to_date_project_is_told_there_is_nothing_to_do (tests.test_adopt.UpdateOutput) ... ok
| test_seat_checkouts_inside_the_project_are_ignored (tests.test_adopt.UpdateOutput) ... ok
| test_a_kept_document_keeps_the_documents_it_links_to (tests.test_adopt.Updates) ... ok
| test_adding_an_adapter_keeps_the_ones_already_installed (tests.test_adopt.Updates) ... ok
| test_crlf_checkout_of_an_unedited_file_counts_as_unedited (tests.test_adopt.Updates) ... ok
| test_dry_run_writes_nothing (tests.test_adopt.Updates) ... ok
| test_files_a_release_drops_are_removed_only_when_provably_unedited (tests.test_adopt.Updates) ... ok
| test_unedited_copies_are_replaced_and_edited_ones_kept (tests.test_adopt.Updates) ... ok
| test_update_with_nothing_changed_writes_nothing (tests.test_adopt.Updates) ... ok
| test_adapters_only_point (tests.test_docs.Budgets) ... ok
| test_copied_set_is_small (tests.test_docs.Budgets) ... ok
| test_word_budgets (tests.test_docs.Budgets) ... ok
| test_a_command_is_told_from_prose (tests.test_docs.Consistency) ... ok
| test_changelog_has_this_release_with_adopter_steps (tests.test_docs.Consistency) ... ok
| test_every_documented_command_exists (tests.test_docs.Consistency) ... ok
| test_legacy_fingerprints_are_well_formed (tests.test_docs.Consistency) ... ok
| test_relative_links_resolve (tests.test_docs.Consistency) ... ok
| test_summary_parts_match_the_worker_card (tests.test_docs.Consistency) ... ok
| test_framework_repository_passes_its_own_project_checks (tests.test_docs.Portability) ... ok
| test_no_personal_paths_or_addresses (tests.test_docs.Portability) ... ok
| test_no_shell_heredocs_in_instructions (tests.test_docs.Portability) ... ok
| test_clean_project_passes (tests.test_fw_checks.ProjectChecks) ... ok
| test_commit_ids_only_under_historical_anchors (tests.test_fw_checks.ProjectChecks) ... ok
| test_merge_rule_must_be_known (tests.test_fw_checks.ProjectChecks) ... ok
| test_only_the_historical_anchors_section_is_exempt (tests.test_fw_checks.ProjectChecks) ... ok
| test_personal_paths_and_emails (tests.test_fw_checks.ProjectChecks) ... ok
| test_personal_pattern_edge_cases (tests.test_fw_checks.ProjectChecks) ... ok
| test_state_budget (tests.test_fw_checks.ProjectChecks) ... ok
| test_status_names_uninitialised_submodules (tests.test_fw_checks.ProjectChecks) ... ok
| test_tool_entry_files_must_point_at_agents (tests.test_fw_checks.ProjectChecks) ... ok
| test_local_edits_to_framework_files_are_listed (tests.test_fw_checks.ReleaseCheck) ... ok
| test_status_reports_a_newer_release (tests.test_fw_checks.ReleaseCheck) ... ok
| test_unreachable_framework_is_unknown_not_an_error (tests.test_fw_checks.ReleaseCheck) ... ok
| test_batch_files_are_scanned (tests.test_fw_checks.ScanScope) ... ok
| test_long_batch_paperwork_is_flagged_but_output_is_not_counted (tests.test_fw_checks.ScanScope) ... ok
| test_round_attachments_are_scanned (tests.test_fw_checks.ScanScope) ... ok
| test_the_personal_data_message_says_which_documents_are_scanned (tests.test_fw_checks.ScanScope) ... ok
| test_commits_on_a_detached_head_are_not_safe_to_leave (tests.test_status.LeavingAMachine) ... ok
| test_leaving_with_unpushed_work_is_not_safe (tests.test_status.LeavingAMachine) ... ok
| test_a_branch_editing_an_existing_batch_file_is_not_called_merged (tests.test_status.WorkNotMerged) ... ok
| test_a_branch_here_and_on_github_is_listed_once (tests.test_status.WorkNotMerged) ... ok
| test_a_cloud_named_branch_is_read_by_its_files (tests.test_status.WorkNotMerged) ... ok
| test_a_merged_branch_left_behind_is_not_shown_as_working (tests.test_status.WorkNotMerged) ... ok
| test_a_release_3_round_is_named_as_one (tests.test_status.WorkNotMerged) ... ok
| test_a_squash_merged_batch_is_not_listed (tests.test_status.WorkNotMerged) ... ok
| test_a_verifier_on_its_own_branch_is_found (tests.test_status.WorkNotMerged) ... ok
| test_brains_own_branch_waits_for_the_owner (tests.test_status.WorkNotMerged) ... ok
| test_each_batch_is_followed_from_working_to_judged (tests.test_status.WorkNotMerged) ... ok
| test_fixes_after_a_review_are_not_shown_as_judged (tests.test_status.WorkNotMerged) ... ok
| test_nothing_waiting_says_so (tests.test_status.WorkNotMerged) ... ok
| test_this_machines_copy_ahead_of_a_merged_github_copy_is_listed (tests.test_status.WorkNotMerged) ... ok
| test_work_in_progress_is_not_called_nothing (tests.test_status.WorkNotMerged) ... ok
| 
| ----------------------------------------------------------------------
| Ran 69 tests in 39.704s
| 
| OK
| exit: 0
| 
| $ python3 -m ruff check --select F,E9,B,UP --target-version py39 tools templates tests
| All checks passed!
| exit: 0
| 
| $ python3 tools/fw.py check
| 0 error(s), 0 warning(s)
| exit: 0
| 
| $ git diff v4.0.1 HEAD -- framework tools templates
| (no output)
| exit: 0
```

## Review-draft failed attempts

Actual output excerpts; the diagnostic filename suffix is omitted to avoid
repeating the command-parsing trigger inside this document. The full-suite
draft and first focused retry both failed before this formatting correction.

```text
| $ python3 -m unittest discover -s tests -t . -v
| FAIL: test_every_documented_command_exists (tests.test_docs.Consistency)
| AssertionError: 'same' not found in {'check', 'status'}
| Ran 69 tests in 40.782s
| FAILED (failures=1)
| exit: 1
|
| $ python3 -m unittest tests.test_docs.Consistency.test_every_documented_command_exists -v
| FAIL: test_every_documented_command_exists (tests.test_docs.Consistency)
| AssertionError: 'same' not found in {'check', 'status'}
| Ran 1 test in 0.007s
| FAILED (failures=1)
| exit: 1
```

## Final review-file validation

Full suite rerun with corrected review present; output excerpt:

```text
| $ python3 -m unittest discover -s tests -t . -v
| 
| ----------------------------------------------------------------------
| Ran 69 tests in 35.057s
| 
| OK
| exit: 0
|
| $ python3 tools/fw.py check
| 0 error(s), 0 warning(s)
| exit: 0
|
| $ git diff --check
| (no output)
| exit: 0
```
