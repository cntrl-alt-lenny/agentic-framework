"""The authority model is what this framework is for. Guard it.

Three things are checked:

1. No normative document contains stale authority language — text routing a
   routine merge back to the owner, or granting an executor the right to accept
   its own work.
2. The guard actually catches the **real** v1 text, preserved verbatim in
   `fixtures/v1_stale_authority.md`. That is a red-before-green proof against a
   known broken state, not against an invented one.
3. The role contracts still state the boundaries they exist to state.

HONESTY NOTE. This repository's product is normative text, so a property of the
text *is* the invariant rather than a proxy for one. What these tests cannot do
is prove that a running agent obeys what the text says; nothing in a repository
can. They prevent the text from silently reverting.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import authority  # noqa: E402
import docset  # noqa: E402


class TestNormativeSurfaceIsClean(unittest.TestCase):
    def test_scan_set_is_not_empty(self):
        # Fail closed. A guard that scanned nothing must not report success.
        self.assertGreaterEqual(
            len(docset.normative_files()), 10,
            "the normative document set collapsed; this guard would pass "
            "vacuously",
        )

    def test_no_stale_authority_language(self):
        problems = []
        for path in docset.normative_files():
            problems += [
                str(f) for f in authority.scan(
                    path.read_text(encoding="utf-8"),
                    source=path.relative_to(ROOT).as_posix(),
                )
            ]
        self.assertEqual(problems, [], "\n".join(problems))

    def test_no_inert_owner_override_declarations(self):
        """A declaration protecting nothing is a silent widening waiting to
        happen -- including one accidentally live inside a documentation
        example of the declaration syntax itself (templates/AGENTS.md)."""
        problems = []
        for path in docset.normative_files():
            text = path.read_text(encoding="utf-8")
            rel = path.relative_to(ROOT).as_posix()
            problems += [
                f"{rel}:{line} owner-override declaration exempts nothing"
                for line in authority.inert_override_declarations(text, source=rel)
            ]
        self.assertEqual(problems, [], "\n".join(problems))

    def test_no_inert_counterexample_blocks(self):
        """`python3 tools/authority.py framework` reported "counterexample
        block suppresses nothing" at framework/evidence.md,
        framework/failure-catalogue.md, framework/git-and-isolation.md,
        framework/topologies.md and framework/adoption.md -- every one of
        them a block declaring a NEUTRALITY violation
        (`guard:violation compound-lane ...`), which this guard's own rules
        never fire on. Never checked against the real documents before; see
        TestCounterexampleBlockOwnership for the synthetic, narrower proofs.
        """
        problems = []
        for path in docset.normative_files():
            text = path.read_text(encoding="utf-8")
            rel = path.relative_to(ROOT).as_posix()
            problems += [
                f"{rel}:{line} counterexample block suppresses nothing"
                for line in authority.inert_counterexamples(text, source=rel)
            ]
        self.assertEqual(problems, [], "\n".join(problems))


class TestCounterexampleBlockOwnership(unittest.TestCase):
    """A block genuinely owned by a DIFFERENT scanner must not be judged
    "inert" here -- but a block this guard genuinely does own, and that
    genuinely exempts nothing, must still be caught. Fixes the class: not
    just the four reported documents, but the general mechanism, proven with
    synthetic cases beyond them.

    Ownership is only ever a TIE-BREAKER for an already-empty scan, never a
    reason to stop looking: a block whose scan finds SOMETHING is not inert
    regardless of which rule its declaration names, because the wrapper is
    genuinely suppressing real content -- exactly the property this check
    exists to prove. Skipping that block just because its declaration names
    a foreign rule would silently lose coverage of real stale-authority text
    that happens to share a block with an unrelated neutrality declaration.
    """

    NEUTRALITY_OWNED = (
        '<!-- guard:counterexample -->\n'
        '<!-- guard:violation compound-lane roles=builder text="Acme Builder" -->\n'
        "Hand this to the Acme Builder.\n"
        "<!-- /guard:counterexample -->\n"
    )

    def test_a_block_declaring_only_a_neutrality_rule_is_not_inert_here(self):
        self.assertEqual(
            authority.inert_counterexamples(self.NEUTRALITY_OWNED), [],
            "a block this guard does not own, and that contains nothing "
            "this guard would ever find, was reported as this guard's own "
            "inert exemption",
        )

    def test_a_block_declaring_only_a_neutrality_rule_produces_no_top_level_finding(self):
        # The wrapper still suppresses the whole block from top-level
        # findings, same as any counterexample block -- ownership filtering
        # only changes what inert_counterexamples() reports, never scan()'s
        # ordinary suppression of wrapped content.
        self.assertEqual(authority.scan(self.NEUTRALITY_OWNED), [])

    def test_a_block_with_a_foreign_declaration_but_real_authority_content_is_not_inert(self):
        """Real stale-authority text sharing a block with an unrelated
        neutrality declaration must still be recognised as "not inert" --
        the wrapper IS suppressing something real, even though it is not
        specifically declared under an authority-shaped rule. Ownership
        filtering must never turn into a way to stop looking at a block's
        actual content.
        """
        body = (
            '<!-- guard:counterexample -->\n'
            '<!-- guard:violation compound-lane roles=builder '
            'text="Acme Builder" -->\n'
            "Hand this to the Acme Builder, who will offer to merge it.\n"
            "<!-- /guard:counterexample -->\n"
        )
        self.assertEqual(
            authority.inert_counterexamples(body), [],
            "a block containing real stale-authority text was reported as "
            "inert merely because its declaration named a different rule",
        )

    def test_a_block_this_guard_genuinely_owns_and_exempts_nothing_is_still_caught(self):
        """The other half of the fix: ownership-filtering must not become a
        way to silence a real defect in this guard's own declarations. Uses
        harmless declared text (not itself stale-shaped) so the assertion
        tests the real prose, not the declaration comment's own wording.
        """
        body = (
            '<!-- guard:counterexample -->\n'
            '<!-- guard:violation routine-approval roles=builder '
            'text="Brain reviews carefully." -->\n'
            "Brain reviews carefully.\n"
            "<!-- /guard:counterexample -->\n"
        )
        self.assertEqual(
            authority.inert_counterexamples(body), [1],
            "a block genuinely declared for this guard's own rule, that "
            "exempts nothing real, must still be caught",
        )

    def test_a_block_this_guard_genuinely_owns_and_does_exempt_something_is_clean(self):
        body = (
            '<!-- guard:counterexample -->\n'
            '<!-- guard:violation routine-approval roles=builder '
            'text="offer to merge" -->\n'
            "Brain will offer to merge once reviewed.\n"
            "<!-- /guard:counterexample -->\n"
        )
        self.assertEqual(authority.inert_counterexamples(body), [])
        self.assertEqual(authority.scan(body), [])


class TestGuardCatchesTheRealV1Text(unittest.TestCase):
    """Red-before-green, against the actual broken state."""

    FIXTURE = ROOT / "tests" / "fixtures" / "v1_stale_authority.md"

    def setUp(self):
        self.text = self.FIXTURE.read_text(encoding="utf-8")
        self.findings = authority.scan(self.text, source="v1")

    def test_fixture_exists_and_is_v1_text(self):
        self.assertIn("HISTORICAL FIXTURE", self.text)

    def test_fixture_is_excluded_from_every_normative_scan(self):
        # If the fixture ever entered the normative set, the suite would fail
        # for the wrong reason and someone would "fix" the fixture.
        self.assertNotIn(
            self.FIXTURE.resolve(),
            {p.resolve() for p in docset.normative_files()},
        )

    def test_every_v1_authority_idiom_is_rejected(self):
        self.assertTrue(self.findings, "the guard found nothing in known-bad text")
        both = {f.rule for f in self.findings}
        self.assertIn("routine-approval", both)
        self.assertIn("executor-self-merge", both)

    def test_the_specific_v1_failures_are_each_caught(self):
        """Named cases, because each was a distinct real defect."""
        matched = " ".join(f.matched.lower() for f in self.findings)
        for needle, why in (
            ("offer to merge", "brain offering a routine merge to the owner"),
            ("execute on ok", "merge conditioned on an approval token"),
            ("merges on the human's ok", "merge conditioned on a person"),
            ("self-merge", "an executor merging its own work"),
        ):
            with self.subTest(case=why):
                self.assertIn(needle, matched, f"v1 defect not caught: {why}")

    def test_owner_named_as_merge_actor_is_caught(self):
        for line in ("Human project owner. Sets priorities, picks direction, "
                     "merges PRs, adds/retires agents.",
                     "You. Sets priorities, picks direction, merges PRs."):
            with self.subTest(line=line[:40]):
                self.assertTrue(
                    authority.scan(line),
                    "the owner named as the routine merge actor was allowed",
                )


class TestNegationIsHandled(unittest.TestCase):
    """Correct documents talk about merging constantly. Both directions."""

    PERMISSIONS = (
        "The scaffolder has production-fire self-merge authority.",
        "Offer to merge, then execute on OK.",
        "Wait for the owner's approval before merging.",
        "The owner merges the PRs.",
    )
    PROHIBITIONS = (
        "Worker and Verifier never merge anything.",
        "An executor does not accept its own work.",
        "You may not merge, under any instruction.",
        "Never self-merge; escalate instead.",
        "Brain does not put a routine merge decision back to the owner.",
        "Any document describing a human per-round merge approval as the gate "
        "is stale.",
    )

    def test_permissions_fire(self):
        for line in self.PERMISSIONS:
            with self.subTest(line=line[:40]):
                self.assertTrue(authority.scan(line), "permission not caught")

    def test_prohibitions_do_not_fire(self):
        for line in self.PROHIBITIONS:
            with self.subTest(line=line[:40]):
                self.assertEqual(
                    [str(f) for f in authority.scan(line)], [],
                    "a correct prohibition was reported as a violation; a guard "
                    "that cries wolf gets disabled by whoever trips it",
                )


class TestOwnerOverride(unittest.TestCase):
    """The owner's standing override now has a recognised, reviewable form.

    Reported by gx-spirit-caller: the same meaning ("Brain merges only after
    the owner's approval") passed or failed depending on phrasing alone, and
    there was no sanctioned place to record it. `<!-- guard:owner-override
    <rule> text="<sentence>" -->` fixes the class, not the one reported
    phrasing -- see `tools/authority.py`'s module docstring.
    """

    def _declared(self, sentence: str, *, rule: str = "routine-approval") -> str:
        return (
            f'<!-- guard:owner-override {rule} text="{sentence}" -->\n{sentence}\n'
        )

    def test_reproduces_the_reported_inconsistency_undeclared(self):
        """The bug report's own two commands, unmodified."""
        flagged = "Brain merges on the owner's approval."
        self.assertTrue(
            authority.scan(flagged),
            "the wording-sensitive phrasing must still be caught when not "
            "declared as an override -- otherwise this stops being the bug",
        )

    def test_the_declared_form_is_recognised_not_judged_by_wording(self):
        doc = self._declared("Brain merges on the owner's approval.")
        self.assertEqual(authority.scan(doc), [], "a declared override must "
                          "not surface as a finding")
        overrides = authority.scan_overrides(doc)
        self.assertTrue(overrides, "the override was not recognised at all")
        self.assertEqual(authority.inert_override_declarations(doc), [])

    def test_a_second_natural_phrasing_of_the_same_policy_is_also_recognised(self):
        """Different wording, same standing decision -- both must work
        uniformly once declared, closing the "passes or fails on phrasing"
        gap rather than fixing one example of it."""
        doc = self._declared(
            "Brain reviews and adjudicates, then merges reviewed work only "
            "on the owner's approval."
        )
        self.assertEqual(authority.scan(doc), [])
        self.assertTrue(authority.scan_overrides(doc))
        self.assertEqual(authority.inert_override_declarations(doc), [])

    def test_override_does_not_silence_an_unrelated_finding_elsewhere(self):
        doc = (
            self._declared("Brain merges on the owner's approval.")
            + "\nElsewhere: the scaffolder offers to merge before Brain decides.\n"
        )
        findings = authority.scan(doc)
        self.assertTrue(
            findings, "the guard must still catch stale language the "
            "override does not govern"
        )
        self.assertTrue(all(f.rule == "routine-approval" for f in findings))
        self.assertIn("offers to merge", " ".join(f.matched for f in findings))

    def test_override_does_not_widen_across_a_different_rule_same_line(self):
        """A declared override for one rule must not blanket-exempt a
        different rule's finding on the same physical line."""
        sentence = (
            "Brain merges on the owner's approval and the executor may "
            "self-merge."
        )
        doc = self._declared(sentence, rule="routine-approval")
        findings = authority.scan(doc)
        self.assertTrue(
            findings, "executor-self-merge on the same line must survive an "
            "override declared only for routine-approval"
        )
        self.assertEqual({f.rule for f in findings}, {"executor-self-merge"})

    def test_inert_when_declared_text_is_not_actually_flagged(self):
        """A blanket exemption cannot be manufactured for harmless prose."""
        doc = self._declared("Brain reviews the work carefully.")
        self.assertEqual(authority.scan_overrides(doc), [])
        self.assertEqual(authority.inert_override_declarations(doc), [1])

    def test_inert_when_declared_rule_does_not_match_the_real_finding(self):
        doc = self._declared(
            "Brain merges on the owner's approval.", rule="executor-self-merge",
        )
        self.assertEqual(authority.scan_overrides(doc), [])
        self.assertEqual(authority.inert_override_declarations(doc), [1])
        # The real finding is untouched -- a wrong-rule declaration protects
        # nothing, and the guard must still catch the actual stale text.
        self.assertTrue(authority.scan(doc))

    def test_inert_when_declared_text_is_a_paraphrase_not_the_real_sentence(self):
        doc = (
            '<!-- guard:owner-override routine-approval '
            'text="Brain merges after the owner says yes." -->\n'
            "Brain merges on the owner's approval.\n"
        )
        self.assertEqual(authority.scan_overrides(doc), [])
        self.assertEqual(authority.inert_override_declarations(doc), [1])
        self.assertTrue(authority.scan(doc))

    def test_inert_when_the_sentence_is_already_a_correct_prohibition(self):
        """Nothing to override when the sentence was never a violation."""
        doc = self._declared("Brain never merges on the owner's approval.")
        self.assertEqual(authority.scan(doc), [])
        self.assertEqual(authority.scan_overrides(doc), [])
        self.assertEqual(authority.inert_override_declarations(doc), [1])

    def test_a_soft_wrapped_override_sentence_is_still_recognised(self):
        sentence = (
            "Brain merges reviewed work only on the owner's approval, "
            "recorded here."
        )
        doc = (
            f'<!-- guard:owner-override routine-approval text="{sentence}" -->\n'
            "Brain merges reviewed work only on the owner's approval, recorded\n"
            "here.\n"
        )
        self.assertEqual(authority.scan(doc), [])
        self.assertTrue(authority.scan_overrides(doc))
        self.assertEqual(authority.inert_override_declarations(doc), [])

    def test_a_declaration_inside_a_fenced_code_example_is_not_live(self):
        """Documentation SHOWING the declaration syntax with placeholder text
        (as templates/AGENTS.md does) must not itself become a live, and
        therefore inert, declaration -- matching general Markdown-example
        practice: fenced code is not scanned for live declarations, the same
        boundary `framework/adoption.md` documents for the unrelated
        branch-namespace declaration.
        """
        doc = (
            "# Docs\n\n"
            "Here is the syntax:\n\n"
            "```text\n"
            + self._declared("<the exact overriding sentence>")
            + "```\n"
        )
        self.assertEqual(authority.scan(doc), [])
        self.assertEqual(authority.scan_overrides(doc), [])
        self.assertEqual(
            authority.inert_override_declarations(doc), [],
            "a fenced-code example of the declaration syntax was treated as "
            "a live, unfulfilled declaration",
        )

    def test_a_real_policy_sentence_inside_a_fence_is_still_flagged(self):
        """Fencing is not a way to hide real stale-authority text: general
        prose scanning does not exempt fenced code (a genuine policy
        statement written inside a code fence would otherwise evade
        detection entirely), only DECLARATION PARSING does. So real
        stale-shaped text inside a fence still surfaces as a finding, and its
        accompanying declaration -- also inside the fence -- earns no
        override, because the declaration itself is not live there.
        """
        doc = (
            "# Docs\n\n```text\n"
            + self._declared("Brain merges on the owner's approval.")
            + "```\n"
        )
        findings = authority.scan(doc)
        self.assertTrue(
            findings, "real stale-authority text inside a fence must still "
            "be caught"
        )
        self.assertEqual(authority.scan_overrides(doc), [])
        self.assertEqual(
            authority.inert_override_declarations(doc), [],
            "a declaration inside a fence must not be reported as an "
            "inert LIVE declaration either -- it was simply never live",
        )

    def test_two_independent_overrides_in_one_document_both_validate(self):
        doc = (
            self._declared("Brain merges on the owner's approval.")
            + "\n"
            + self._declared(
                "The scaffolder may self-merge hotfixes.",
                rule="executor-self-merge",
            )
        )
        self.assertEqual(authority.scan(doc), [])
        overrides = authority.scan_overrides(doc)
        self.assertEqual({f.rule for f in overrides},
                          {"routine-approval", "executor-self-merge"})
        self.assertEqual(authority.inert_override_declarations(doc), [])

    def test_the_declaration_marker_itself_is_not_double_counted(self):
        """The HTML comment repeats the sentence in its own text= attribute;
        that must not produce a second, unsuppressible finding on the
        marker's own line."""
        doc = self._declared("Brain merges on the owner's approval.")
        findings = authority.scan(doc)
        self.assertEqual(findings, [])
        overrides = authority.scan_overrides(doc)
        self.assertTrue(all(f.line == 2 for f in overrides), overrides)

    def test_cli_reports_the_declared_form_as_clean_and_distinct(self):
        import subprocess
        import sys
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.md"
            path.write_text(
                "# A\n\n" + self._declared("Brain merges on the owner's approval."),
                encoding="utf-8",
            )
            proc = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "authority.py"), str(path)],
                capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertIn("recognised owner override", proc.stdout)

    def test_cli_still_fails_on_the_undeclared_phrasing(self):
        import subprocess
        import sys
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.md"
            path.write_text(
                "# A\n\nBrain merges on the owner's approval.\n", encoding="utf-8",
            )
            proc = subprocess.run(
                [sys.executable, str(ROOT / "tools" / "authority.py"), str(path)],
                capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)


class TestRoleContractsStateTheirBoundaries(unittest.TestCase):
    def test_executor_contracts_prohibit_merging(self):
        for role in ("worker", "verifier"):
            with self.subTest(role=role):
                text = (ROOT / "framework" / "roles" / f"{role}.md").read_text(
                    encoding="utf-8"
                )
                self.assertTrue(
                    authority.has_merge_prohibition(text),
                    f"{role}.md no longer states that it does not merge",
                )

    def test_brain_contract_claims_the_routine_merge(self):
        text = (ROOT / "framework" / "roles" / "brain.md").read_text(encoding="utf-8")
        claims = [
            line for line in text.splitlines()
            if "Brain" in line
            and ("merges" in line or "merge it" in line)
            and not authority.NEGATORS.search(line[:line.find("merge")])
        ]
        self.assertTrue(
            claims,
            "brain.md must positively state that Brain performs the routine "
            "merge; without it the framework has no acceptance authority",
        )

    def test_constitution_reserves_actions_to_the_owner(self):
        text = (ROOT / "framework" / "CONSTITUTION.md").read_text(encoding="utf-8")
        self.assertIn(
            "Owner-reserved actions", text,
            "delegated merge authority without a reserved list is unbounded",
        )
        for reserved in ("force-push", "branch protection", "licensing"):
            with self.subTest(item=reserved):
                self.assertIn(reserved, text)


class TestReservedListStaysNarrow(unittest.TestCase):
    """A reserved list too wide is the same defect as no delegation at all.

    Delegating routine acceptance and then reserving every technical act it
    implies gives the authority back one question at a time. The list once
    reserved "deleting branches" and "changing CI" outright, which put routine
    housekeeping and ordinary engineering work back on the owner.

    So the categories are locked in BOTH directions: the destructive and
    governing forms must still be reserved, and the unqualified forms must not
    come back.

    HONESTY NOTE. This reads the reserved list out of the constitution by its
    heading, so it is structural rather than a proxy — but it is a text guard on
    a text artifact, like every other guard here. It cannot prove a running
    Brain honours the distinction.
    """

    CONSTITUTION = ROOT / "framework" / "CONSTITUTION.md"
    MARKER = "**Owner-reserved actions.**"

    def setUp(self):
        self.text = self.CONSTITUTION.read_text(encoding="utf-8")
        self.block = self._reserved_block(self.text)

    def _reserved_block(self, text: str) -> str:
        start = text.find(self.MARKER)
        self.assertNotEqual(start, -1, "the reserved list has no heading")
        rest = text[start:]
        end = rest.find("\n\n**", len(self.MARKER))
        return rest if end == -1 else rest[:end]

    def test_the_block_was_actually_found(self):
        # Fail closed: an empty block would make every rule below vacuous.
        self.assertGreaterEqual(
            len([l for l in self.block.splitlines() if l.startswith("- ")]), 3,
            "the reserved list could not be read; these guards would pass "
            "having checked nothing",
        )

    def test_destructive_and_governing_actions_are_still_reserved(self):
        for phrase in (
            "force-pushing", "protected branch", "unmerged work",
            "branch protection", "remotes", "licensing",
        ):
            with self.subTest(reserved=phrase):
                self.assertIn(
                    phrase, self.block,
                    "narrowing the list must not drop what genuinely belongs "
                    "to the owner",
                )

    def test_whole_categories_of_routine_work_are_not_reserved(self):
        """The over-broad forms, named exactly, so they cannot come back."""
        for phrase, why in (
            ("deleting branches",
             "routine deletion of an already-merged task branch is Brain's "
             "housekeeping; only destructive deletion is reserved"),
            ("changing CI",
             "ordinary work on the project's checks is normal reviewed project "
             "work; only what is *enforced* is reserved"),
        ):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase.lower(), self.block.lower(), why)

    def test_the_routine_side_is_stated_not_merely_implied(self):
        """A narrowing nobody can find is a narrowing that does not hold.

        The reader who needs this is a cold Brain deciding whether to delete a
        merged branch. It has to be written down, next to the reserved list.
        """
        for phrase in ("already merged", "housekeeping"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase.lower(), self.text.lower())

    def test_red_or_unreviewed_work_is_refused_rather_than_escalated(self):
        """Brain cannot accept it. That is not the same as asking the owner.

        Listing it as an owner-reserved action made it an escalation, which
        turns the acceptance test into a question — the same defect as an offer
        to merge, from the other side.
        """
        self.assertNotIn(
            "merging work that has not", self.block.lower(),
            "unreviewed or red work is not an owner decision to surface; Brain "
            "cannot accept it",
        )
        self.assertIn("Brain cannot accept it", self.text)


if __name__ == "__main__":
    unittest.main()
