"""Lane identity must derive from roles, never from a provider.

Every rule here is a POSITIVE invariant over the declared role vocabulary, and
fails closed on anything unrecognised. No detector knows a provider name. The
proof is `TestNovelProviderIsRejected`, which uses a name appearing nowhere else
in this repository: if the guard only worked by recognising today's providers,
that name would sail through.

Historical documents are out of scope by design, and the scope split is itself
tested — a policy file cannot be exempted by adding it to a list.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import docset  # noqa: E402
import neutrality  # noqa: E402
import textblocks  # noqa: E402

#: Declared once, in tools/docset.py, and imported everywhere else.
ROLES = docset.ROLES
COORDINATOR = docset.COORDINATOR

#: A name that must appear nowhere else in this repository.
NOVEL = "NebulaAI"


class TestScopeSplitIsHonest(unittest.TestCase):
    def test_normative_set_is_not_empty(self):
        self.assertGreaterEqual(
            len(docset.normative_files()), 10,
            "fail closed: a guard that scanned nothing must not pass",
        )

    def test_normative_and_historical_are_disjoint(self):
        normative = {p.resolve() for p in docset.normative_files()}
        historical = {p.resolve() for p in docset.historical_files()}
        self.assertEqual(normative & historical, set())

    def test_every_historical_file_declares_itself_historical(self):
        # Prevents the exemption list being used to quietly exempt a policy
        # document: doing so would require writing the marker into it.
        for path in docset.historical_files():
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file(), f"stale exemption: {path}")
                self.assertIn(
                    docset.HISTORICAL_MARKER,
                    path.read_text(encoding="utf-8").lower(),
                    "a file exempted from the normative scans must say so in "
                    "its own text",
                )

    def test_every_document_is_classified(self):
        """No third category. A new document is normative by default.

        Escaping the scans requires adding a file to HISTORICAL *and* writing
        the marker into it, or declaring it a fixture — both visible acts.
        CHANGELOG.md was briefly in neither set, which is exactly the hole this
        closes.
        """
        stray = [p.relative_to(ROOT).as_posix() for p in docset.unclassified()]
        self.assertEqual(
            stray, [],
            f"unclassified documents (neither normative, historical, nor a "
            f"declared fixture): {stray}",
        )

    def test_new_framework_documents_are_scanned_by_default(self):
        scanned = {p.resolve() for p in docset.normative_files()}
        exempt = {p.resolve() for p in docset.historical_files()}
        for path in docset.tracked_markdown_files():
            if ROOT / "framework" not in path.parents:
                continue
            with self.subTest(path=path.name):
                self.assertIn(path.resolve(), scanned | exempt)


class TestNormativeSurfaceIsRoleBased(unittest.TestCase):
    def _scan(self, path: Path) -> neutrality.ScanResult:
        return neutrality.scan(
            path.read_text(encoding="utf-8"), ROLES,
            source=path.relative_to(ROOT).as_posix(), coordinator=COORDINATOR,
        )

    def test_declared_role_branch_placeholder_is_not_a_provider_namespace(self):
        for text in (
            "Push your work on builder/<scope> and open a pull request.",
            "Push your work on `builder/<scope>` and open a pull request.",
            "Push your work on builder/feature-42 and open a pull request.",
            "Push your work on `builder/feature-42` and open a pull request.",
        ):
            with self.subTest(text=text):
                self.assertEqual(neutrality.scan(text, ROLES).findings, [])

    def test_declared_structural_branch_namespaces_are_allowed(self):
        text = (
            "Create branch `m3/feature-work` for the next milestone.\n"
            "Keep branch namespace `meta/coordination` for project structure.\n"
        )
        self.assertEqual(
            neutrality.scan(
                text, ("builder", "verifier"),
                branch_namespaces=("m<N>", "meta"),
            ).findings,
            [],
        )

    def test_undeclared_or_unbounded_branch_namespaces_still_fail(self):
        text = "Create `vendor/release` as a branch namespace.\n"
        self.assertTrue(
            any(
                finding.rule == "branch-namespace"
                for finding in neutrality.scan(
                    text, ("builder", "verifier"),
                    branch_namespaces=("m<N>", "meta"),
                ).findings
            )
        )
        with self.assertRaisesRegex(ValueError, "unsupported"):
            neutrality.branch_namespace_declarations(
                '<!-- guard:branch-namespaces prefixes="m<N>,vendor" -->'
            )
        self.assertEqual(
            neutrality.branch_namespace_declarations(
                '```text\n<!-- guard:branch-namespaces prefixes="m<N>,meta" -->\n```'
            ),
            (),
        )

    def test_capitalised_roles_in_adjacent_sentences_are_not_one_lane(self):
        for text in (
            "Hand the report to the Verifier. That Builder then waits.",
            "The Builder finished. Verifier reviews the exact commit.",
            "A Worker stops here! The Verifier continues independently.",
        ):
            with self.subTest(text=text):
                self.assertEqual(neutrality.scan(text, ROLES).findings, [])

    def test_dotted_qualifiers_before_roles_are_rejected(self):
        cases = (
            "Hand the brief to the Mosaic.io Builder.",
            "Route the result to the Rho7.4 Verifier after review.",
            "The North Star.dev Researcher owns the evidence note.",
            "Use the Ember2.0 Scaffolder for this setup step.",
            "A Quartz.site Worker wrote the first draft.",
        )
        for text in cases:
            with self.subTest(text=text):
                findings = neutrality.scan(text, ROLES).findings
                self.assertTrue(
                    any(f.rule == "compound-lane" for f in findings),
                    f"dotted provider-shaped qualifier was not rejected: {text}",
                )

    def test_capitalised_hyphenated_compounds_before_roles_are_clean(self):
        cases = (
            "Self-contained Builder prompts are short.",
            "The Follow-up Builder brief is ready.",
            "Keep the Cross-team Verifier note nearby.",
            "A North-facing Worker checklist is useful.",
            "Use the Post-review Researcher summary.",
            "The High-level Scaffolder guidance is ordinary prose.",
        )
        for text in cases:
            with self.subTest(text=text):
                self.assertEqual(neutrality.scan(text, ROLES).findings, [])

    def test_prefixed_lane_requires_identity_context_not_token_shape(self):
        clean = (
            "The deck-builder UI is separate.",
            "A world-builder tool is documented.",
            "See deck-builder-ui.md for details.",
            "See ../edopro-next-builder for details.",
            "The record-builder module is ordinary text.",
            "A self-builder pattern appears in the manual.",
        )
        caught = (
            "The vendor-builder lane is isolated.",
            "Use the `vendor-builder` queue.",
            "Create vendor-builder/queue for this seat.",
            "The vendor-builder worktree is separate.",
            "Send the task to vendor-builder.",
            "Route the result through vendor-builder role.",
        )
        for text in clean:
            with self.subTest(text=text):
                self.assertEqual(neutrality.scan(text, ROLES).findings, [])
        for text in caught:
            with self.subTest(text=text):
                self.assertTrue(
                    any(
                        finding.rule == "prefixed-lane"
                        for finding in neutrality.scan(text, ROLES).findings
                    ),
                    text,
                )

    def test_no_provider_shaped_lane_identity(self):
        problems: list[str] = []
        for path in docset.normative_files():
            problems += [str(f) for f in self._scan(path).findings]
        self.assertEqual(problems, [], "\n".join(problems))

    def test_counterexample_blocks_do_not_hide_real_violations(self):
        """Suppression must be scoped to the marked block, nothing wider.

        Joint honesty of the blocks themselves — that each is rejected by at
        least one guard — is checked once in `test_guard_honesty.py`, because
        the marker is shared between guards and a block may exist for either.
        """
        import textblocks
        for path in docset.all_documents():
            rel = path.relative_to(ROOT).as_posix()
            text = path.read_text(encoding="utf-8")
            opens = text.count(textblocks.COUNTEREXAMPLE_OPEN)
            closes = text.count(textblocks.COUNTEREXAMPLE_CLOSE)
            with self.subTest(path=rel):
                # An unclosed block suppresses everything to end of file, which
                # would silently disable the guard for the rest of the document.
                self.assertEqual(
                    opens, closes,
                    "unbalanced counterexample markers: an unclosed block "
                    "suppresses the rest of the file",
                )

    def test_counterexample_probe_handles_an_unlisted_specialist_role(self):
        body = (
            '<!-- guard:violation compound-lane roles=decomper '
            'text="Claude Decomper" -->\n'
            "- `Claude Decomper` and `Codex Decomper` as two lanes — that is "
            "one Decomper, run twice.\n"
        )
        findings = neutrality.scan_counterexample(body, ("builder",))
        self.assertTrue(
            any(f.rule == "compound-lane" for f in findings),
            "a marked example must be checked even when it quotes an unlisted "
            "specialist role",
        )

    def test_counterexample_probe_still_leaves_harmless_text_inert(self):
        for body in (
            "Think of the follow-up as a queue of small tasks.\n",
            "Keep the pre-push hook as a branch guard.\n",
            "The e-mail list serves as a queue.\n",
            "Store long-term notes as a branch of the wiki.\n",
            "Treat well-known names as a role hint.\n",
            "This role illustrates role-based delegation.\n",
            "Each branch uses a well-known best-practice layout.\n",
            "The role of a long-term plan is explained here.\n",
            "A queue of ordinary tasks is drained overnight.\n",
            "Namespace collisions are documented in the glossary.\n",
            "The lane is a metaphor for sequence, not a standing seat.\n",
            "Use `well-known` names in prose.\n",
            "The queue records ordinary work items.\n",
            "A branch of the documentation tree is useful.\n",
            "Role-based access is described in the policy.\n",
            "The namespace is reserved for examples.\n",
            "The follow-up lane is a step in the process.\n",
            "A well-known queue name appears in a quotation.\n",
            "The long-term branch plan is archived.\n",
            "This role's scope is intentionally narrow.\n",
            "The pre-push branch guard is documented.\n",
            "A task lane marks sequence in the diagram.\n",
        ):
            with self.subTest(body=body):
                self.assertEqual(neutrality.scan_counterexample(
                    body, ("builder", "verifier")
                ), [])

    def test_counterexample_probe_catches_lane_syntax_beyond_declared_roles(self):
        for body, rule in (
            (
                '<!-- guard:violation compound-lane roles=builder '
                'text="Hand it to the Acme Builder." -->\n'
                "Hand it to the Acme Builder.\n",
                "compound-lane",
            ),
            (
                '<!-- guard:violation prefixed-lane roles=builder '
                'text="Use the `codex-builder` queue." -->\n'
                "Use the `codex-builder` queue.\n",
                "prefixed-lane",
            ),
            (
                '<!-- guard:violation branch-namespace roles=builder '
                'text="Cut `acme/some-scope` for this branch." -->\n'
                "Cut `acme/some-scope` for this branch.\n",
                "branch-namespace",
            ),
            (
                '<!-- guard:violation prefixed-lane roles=scaffolder '
                'text="Use `codex-scaffolder` as a queue name." -->\n'
                "Use `codex-scaffolder` as a queue name.\n",
                "prefixed-lane",
            ),
        ):
            with self.subTest(body=body):
                findings = neutrality.scan_counterexample(
                    body, ("builder", "verifier")
                )
                self.assertTrue(
                    any(f.rule == rule for f in findings),
                    f"{body!r} was not reported as {rule}: {findings}",
                )

    def test_counterexample_declarations_cover_adversarial_real_violations(self):
        cases = (
            ("compound-lane", "builder", "Hand it to the Acme Builder."),
            ("prefixed-lane", "builder", "Use the `codex-builder` queue."),
            ("branch-namespace", "builder", "Cut `acme/some-scope` for this branch."),
            ("prefixed-lane", "scaffolder", "Send the task to `codex-scaffolder`."),
            ("prefixed-lane", "researcher", "Use the `gemini-researcher` queue."),
            ("prefixed-lane", "researcher", "Route everything through the claude-researcher lane."),
            ("prefixed-lane", "scaffolder", "Use the `codex-scaffolder` queue."),
            ("branch-namespace", "decomper", "Cut `claude-decomper/fix-123` for this."),
            ("compound-lane", "scaffolder", "Hand it to the Acme Scaffolder."),
            ("compound-lane", "reviewer", "Send this to the Polaris Reviewer."),
            ("prefixed-lane", "worker", "Use the `orbit-worker` queue."),
            ("branch-namespace", "builder", "Create `nova/release` as a branch namespace."),
            ("compound-lane", "researcher", "Hand it to the Polaris Researcher."),
            ("compound-lane", "worker", "Route this to the Delta Worker."),
            ("compound-lane", "decomper", "Assign the Acme Decomper."),
            ("prefixed-lane", "verifier", "Use the `nebula-verifier` queue."),
            ("prefixed-lane", "researcher", "Route it through the `orion-researcher` lane."),
            ("prefixed-lane", "scaffolder", "Send it to the `atlas-scaffolder` queue."),
            ("branch-namespace", "builder", "Cut `quasar-builder/issue-42` for this."),
            ("branch-namespace", "researcher", "Create `atlas-researcher/design` as a branch namespace."),
            ("prefixed-lane", "decomper", "Use the `lumen-decomper` lane."),
            ("prefixed-lane", "verifier", "Send it to the `nova-verifier` queue."),
        )
        for rule, declared_roles, offending in cases:
            declaration = (
                f'<!-- guard:violation {rule} roles={declared_roles} '
                f'text="{offending}" -->\n{offending}\n'
            )
            with self.subTest(offending=offending):
                findings = neutrality.scan_counterexample(
                    declaration, ("builder", "verifier")
                )
                self.assertTrue(
                    any(f.rule == rule for f in findings),
                    f"{offending!r} was not reported as {rule}: {findings}",
                )

    def test_counterexample_declaration_must_be_present_and_true(self):
        cases = (
            "Hand it to the Acme Builder.\n",
            '<!-- guard:violation compound-lane roles=builder text="Absent Builder" -->\n'
            "Hand it to the Acme Builder.\n",
            '<!-- guard:violation prefixed-lane roles=builder text="Hand it to the Acme Builder." -->\n'
            "Hand it to the Acme Builder.\n",
            '<!-- guard:violation branch-namespace roles=builder text="The queue is ordinary." -->\n'
            "The queue is ordinary.\n",
        )
        for body in cases:
            with self.subTest(body=body):
                self.assertEqual(
                    neutrality.scan_counterexample(body, ("builder", "verifier")),
                    [],
                )

    def test_counterexample_declaration_must_match_its_own_finding(self):
        body = (
            '<!-- guard:violation compound-lane roles=builder text="harmless" -->\n'
            "This is harmless prose.\n"
            "Hand it to the Acme Builder.\n"
        )
        self.assertEqual(
            neutrality.scan_counterexample(body, ("builder", "verifier")), []
        )

    def test_framework_topologies_counterexample_is_noninert_for_builder_verifier(self):
        text = (ROOT / "framework" / "topologies.md").read_text(encoding="utf-8")
        blocks, _ = textblocks.counterexample_blocks(text)
        self.assertTrue(blocks, "topologies.md must contain a counterexample block")
        findings = [
            finding
            for _, body in blocks
            for finding in neutrality.scan_counterexample(
                body, ("builder", "verifier")
            )
        ]
        self.assertTrue(findings, "topologies.md counterexample became inert")

    def test_scan_records_an_unlisted_specialist_counterexample_as_noninert(self):
        text = (
            "<!-- guard:counterexample -->\n"
            '<!-- guard:violation compound-lane roles=decomper '
            'text="Claude Decomper" -->\n'
            "- `Claude Decomper` as a lane.\n"
            "<!-- /guard:counterexample -->\n"
        )
        result = neutrality.scan(text, ("builder",))
        self.assertTrue(result.counterexamples[0].findings)
        self.assertEqual(result.inert_counterexamples(), [])

    def test_adapters_do_not_redefine_the_contract(self):
        problems: list[str] = []
        for path in docset.normative_files():
            problems += [
                str(f) for f in neutrality.scan_adapter_blocks(
                    path.read_text(encoding="utf-8"),
                    source=path.relative_to(ROOT).as_posix(),
                )
            ]
        self.assertEqual(problems, [], "\n".join(problems))


class TestGrammarAllowanceCannotBecomeAVendorList(unittest.TestCase):
    """The one allowance in the scanner, guarded."""

    def test_every_qualifier_is_a_lowercase_word(self):
        for word in neutrality.GRAMMAR_QUALIFIERS:
            with self.subTest(word=word):
                self.assertEqual(word, word.lower())
                self.assertTrue(
                    word.replace("'", "").isalpha(),
                    "qualifiers are English function words, not identifiers",
                )

    def test_no_known_provider_smuggled_in(self):
        """Secondary layer, and deliberately so.

        This is the only place a provider name appears, and it guards the
        exemption list rather than the documents. The structural rules do the
        real work; deleting this would weaken the guard but not break its
        architecture.
        """
        for name in ("claude", "anthropic", "codex", "openai", "gpt", "gemini",
                     "google", "grok", "xai", "copilot", "llama", "mistral"):
            with self.subTest(name=name):
                self.assertNotIn(name, neutrality.GRAMMAR_QUALIFIERS)


class TestNovelProviderIsRejected(unittest.TestCase):
    """The demonstration: a name nobody has seen is still rejected."""

    def test_the_novel_name_is_absent_from_the_scanner(self):
        source = (ROOT / "tools" / "neutrality.py").read_text(encoding="utf-8")
        self.assertNotIn(
            NOVEL.lower(), source.lower(),
            "the scanner must not know this name; if it does, this test proves "
            "nothing about future providers",
        )

    def test_the_novel_name_is_absent_from_the_documents(self):
        # If it were already in the tree, "it gets rejected" would prove nothing.
        hits = [
            p.relative_to(ROOT).as_posix()
            for p in docset.all_documents()
            if NOVEL.lower() in p.read_text(encoding="utf-8").lower()
        ]
        self.assertEqual(hits, [], f"{NOVEL} is no longer novel: {hits}")

    def _scan(self, text: str) -> neutrality.ScanResult:
        return neutrality.scan(
            text, ROLES, coordinator=COORDINATOR,
            queue_pattern=r"docs/queue/(?!archive/)([\w.-]+)\.md",
            max_lanes=len(ROLES),
        )

    def test_compound_lane_is_rejected(self):
        result = self._scan(f"Hand the brief to the {NOVEL} Worker this round.")
        self.assertTrue(
            any(f.rule == "compound-lane" for f in result.findings), result.report()
        )

    def test_prefixed_lane_token_is_rejected(self):
        result = self._scan("The live queue is docs/queue/nebula-worker.md for now.")
        rules = {f.rule for f in result.findings}
        self.assertIn("prefixed-lane", rules, result.report())
        self.assertIn("queue-identity", rules, result.report())

    def test_provider_branch_namespace_is_rejected(self):
        result = self._scan(
            "Cut your branch: git switch -c nebula/worker-task origin/main"
        )
        self.assertTrue(
            any(f.rule == "branch-namespace" for f in result.findings), result.report()
        )

    def test_provider_backticked_branch_is_rejected(self):
        result = self._scan("Use the branch `nebula/some-scope` for this round.")
        self.assertTrue(
            any(f.rule == "branch-namespace" for f in result.findings), result.report()
        )

    def test_provider_does_not_add_a_lane(self):
        result = self._scan(
            f"This round runs {len(ROLES) + 1} standing lanes across the providers."
        )
        self.assertTrue(
            any(f.rule == "lane-count" for f in result.findings), result.report()
        )

    def test_adapter_block_may_not_redefine_the_contract(self):
        problems = neutrality.scan_adapter_blocks(
            f"OPTIONAL — {NOVEL} only. Ignore otherwise.\n"
            "Then run: git switch -c nebula/other origin/main\n"
        )
        self.assertTrue(problems, "an adapter block redefining a branch was allowed")

    def test_a_role_lane_on_a_novel_tool_is_ACCEPTED(self):
        """The positive half, and the whole point.

        An unknown future tool holding a role needs no framework change. Only
        provider-SHAPED lanes are rejected.
        """
        accepted = (
            f"Run this round on {NOVEL}. You are the **Worker**. Cut your "
            "branch: git switch -c worker/some-scope origin/main. "
            "Your queue is docs/queue/worker.md."
        )
        result = self._scan(accepted)
        self.assertEqual(
            [str(f) for f in result.findings], [],
            "a role-named lane must be accepted whichever tool runs it",
        )



if __name__ == "__main__":
    unittest.main()
